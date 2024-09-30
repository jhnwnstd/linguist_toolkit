import yt_dlp
from pathlib import Path
import unicodedata
import re
import logging
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration options
VERBOSE = False  # Toggle True for verbose output
MAX_WORKERS = 8  # Number of threads for concurrent downloads

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for filename sanitization
ILLEGAL_CHAR_PATTERN = re.compile(r'[^\w\s-]')
SPACE_PATTERN = re.compile(r'\s+')
YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.)?'
    r'(youtube\.com/watch\?v=|youtube\.[a-z]{2,3}/watch\?v=|youtu\.be/)'
    r'[^&\s]+$',
    re.IGNORECASE
)

class YouTubeDownloader:
    def __init__(self, 
                 download_folder: str = "Downloaded_Videos", 
                 verbose: bool = False, 
                 max_workers: int = MAX_WORKERS):
        """
        Initializes the YouTubeDownloader with specified settings.

        Args:
            download_folder (str): Directory where videos will be downloaded.
            verbose (bool): Enable verbose logging.
            max_workers (int): Number of threads for concurrent downloads.
        """
        self.download_path = Path(download_folder)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.max_workers = max_workers

        # Update logger level based on verbosity
        if self.verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """Validate if the provided URL is a valid YouTube video URL."""
        return bool(YOUTUBE_URL_REGEX.match(url.strip()))

    @staticmethod
    def sanitize_filename(title: str, max_length: int = 255) -> str:
        """
        Sanitize a string to create a safe and clean filename.

        Args:
            title (str): Original title of the video.
            max_length (int): Maximum allowed length for the filename.

        Returns:
            str: Sanitized filename.
        """
        sanitized_title = unicodedata.normalize('NFKD', title)
        sanitized_title = ILLEGAL_CHAR_PATTERN.sub('', sanitized_title)
        sanitized_title = SPACE_PATTERN.sub('_', sanitized_title).strip(".")
        sanitized_title = sanitized_title.encode('utf-8')[:max_length].decode('utf-8', 'ignore').rstrip('_')
        return unicodedata.normalize('NFC', sanitized_title)

    def get_cookies_file(self) -> Optional[Path]:
        """
        Prompt the user to provide the path to the cookies.txt file or use the default in the working directory.

        Returns:
            Optional[Path]: Path to the cookies.txt file or None.
        """
        default_cookies_path = Path.cwd() / "cookies.txt"
        if default_cookies_path.exists():
            use_default = input(f"Found 'cookies.txt' in the current directory. Use it? (y/n): ").strip().lower()
            if use_default == 'y':
                logger.debug(f"Using default cookies file: {default_cookies_path}")
                return default_cookies_path
        else:
            logger.debug("No 'cookies.txt' found in the current directory.")

        cookies_path_input = input("Enter the path to your 'cookies.txt' file (or press Enter to skip): ").strip()
        if cookies_path_input:
            cookies_file = Path(cookies_path_input)
            if cookies_file.exists():
                logger.debug(f"Using provided cookies file: {cookies_file}")
                return cookies_file
            else:
                logger.warning(f"Cookies file '{cookies_file}' not found.")
        else:
            logger.info("Proceeding without cookies. Some videos may require authentication.")

        return None

    def download_video(self, video_url: str, cookies_file: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Download a single YouTube video using yt-dlp, ensuring the output is an MP4 file.

        Args:
            video_url (str): URL of the YouTube video.
            cookies_file (Optional[Path]): Path to the cookies.txt file for authentication.

        Returns:
            Tuple[bool, str]: Success status and message.
        """
        if not self.is_valid_youtube_url(video_url):
            logger.error(f"Invalid URL: {video_url}")
            return False, f"Invalid URL: {video_url}"

        # Prepare yt-dlp options to ensure MP4 output
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'quiet': not self.verbose,
            'no_warnings': not self.verbose,
            'merge_output_format': 'mp4',  # Ensure the final output is MP4
            'cookiefile': str(cookies_file) if cookies_file else None,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.debug(f"Starting download for: {video_url}")
                info_dict = ydl.extract_info(video_url, download=True)
                title = self.sanitize_filename(info_dict.get('title', 'video'))
                ext = 'mp4'  # Ensure extension is mp4
                video_file = self.download_path / f"{title}.{ext}"

                if video_file.exists():
                    logger.info(f"Successfully downloaded: '{video_file}'")
                    return True, f"Downloaded: {title}"
                else:
                    logger.error(f"Download completed but file not found: '{video_file}'")
                    return False, f"Download completed but file not found: {title}"

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Error downloading {video_url}: {e}")
            return False, f"Error downloading {video_url}: {e}"

    def download_videos_from_file(self, file_path: str, cookies_file: Optional[Path] = None) -> None:
        """
        Download multiple YouTube videos listed in a file concurrently.

        Args:
            file_path (str): Path to the file containing YouTube URLs.
            cookies_file (Optional[Path]): Path to the cookies.txt file for authentication.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"'{file_path.name}' not found. Creating the file for you to add video URLs.")
            file_path.touch()
            return

        urls = [line.strip() for line in file_path.read_text().splitlines() if self.is_valid_youtube_url(line.strip())]
        if not urls:
            logger.warning(f"No valid video URLs found in '{file_path.name}'.")
            return

        logger.info(f"Starting downloads for {len(urls)} video(s)...")

        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.download_video, url, cookies_file): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, message = future.result()
                    status = "Success" if success else "Failed"
                    logger.info(f"[{status}] {message}")
                except Exception as e:
                    logger.error(f"[Failed] Exception occurred while downloading {url}: {e}")

        logger.info("Download session completed.")

    def run_ui(self) -> None:
        """
        User Interface function to handle user input and execute corresponding actions.
        """
        logger.info("\nWelcome to the YouTube Video Downloader")
        while True:
            print("\nSelect an option:")
            print("(1) Download a YouTube video")
            print("(2) Download videos from urls.txt")
            print("(3) Quit")
            user_input = input("Enter 1, 2, or 3: ").strip().lower()

            if user_input in ('3', 'quit'):
                logger.info("Exiting the program. Goodbye!")
                break
            elif user_input == '2':
                file_path = Path.cwd() / "urls.txt"
                cookies_file = self.get_cookies_file()
                self.download_videos_from_file(str(file_path), cookies_file=cookies_file)
            elif user_input == '1':
                video_url = input("Enter the YouTube video URL: ").strip()
                if self.is_valid_youtube_url(video_url):
                    cookies_file = self.get_cookies_file()
                    success, message = self.download_video(
                        video_url, cookies_file=cookies_file
                    )
                    if success:
                        logger.info(message)
                    else:
                        logger.error(f"Failed to download: {message}")
                else:
                    logger.error("Invalid URL. Please enter a valid YouTube video URL.")
            else:
                logger.warning("Invalid option. Please enter 1, 2, or 3.")

def main():
    downloader = YouTubeDownloader(verbose=VERBOSE)
    downloader.run_ui()

if __name__ == "__main__":
    main()