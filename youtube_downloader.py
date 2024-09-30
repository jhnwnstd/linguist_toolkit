import yt_dlp
from pathlib import Path
import unicodedata
import re
import logging
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration options
VERBOSE = False  # Toggle to True for verbose output
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
                 video_folder: str = "Downloaded_Videos",
                 audio_folder: str = "Downloaded_Audio",
                 verbose: bool = False, 
                 max_workers: int = MAX_WORKERS):
        """
        Initializes the YouTubeDownloader with specified settings.

        Args:
            video_folder (str): Directory where videos will be saved.
            audio_folder (str): Directory where audio files will be saved.
            verbose (bool): Enable verbose logging.
            max_workers (int): Number of threads for concurrent downloads.
        """
        self.video_path = Path(video_folder)
        self.audio_path = Path(audio_folder)
        self.video_path.mkdir(parents=True, exist_ok=True)
        self.audio_path.mkdir(parents=True, exist_ok=True)
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

    def download_video_and_audio(self, video_url: str, cookies_file: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Download a single YouTube video as MP4 and extract audio as WAV, saving them in different folders.

        Args:
            video_url (str): URL of the YouTube video.
            cookies_file (Optional[Path]): Path to the cookies.txt file for authentication.

        Returns:
            Tuple[bool, str]: Success status and message.
        """
        if not self.is_valid_youtube_url(video_url):
            logger.error(f"Invalid URL: {video_url}")
            return False, f"Invalid URL: {video_url}"

        # Prepare yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'paths': {
                'video': str(self.video_path),
                'audio': str(self.audio_path),
            },
            'quiet': not self.verbose,
            'no_warnings': not self.verbose,
            'merge_output_format': 'mp4',
            'cookiefile': str(cookies_file) if cookies_file else None,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.debug(f"Starting download for: {video_url}")
                info_dict = ydl.extract_info(video_url, download=True)
                title = self.sanitize_filename(info_dict.get('title', 'video'))

                # Video file
                video_file = self.video_path / f"{title}.mp4"
                if not video_file.exists():
                    logger.error(f"Download completed but video file not found: '{video_file}'")
                    return False, f"Download completed but video file not found: {title}"

                # Audio file
                audio_file = self.audio_path / f"{title}.wav"
                if not audio_file.exists():
                    logger.error(f"Audio extraction completed but file not found: '{audio_file}'")
                    return False, f"Audio extraction completed but file not found: {title}"

                logger.info(f"Successfully downloaded video and extracted audio for: '{title}'")
                return True, f"Downloaded and processed: {title}"

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Error downloading {video_url}: {e}")
            return False, f"Error downloading {video_url}: {e}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, f"Unexpected error: {e}"

    def download_videos_from_file(self, file_path: str, cookies_file: Optional[Path] = None) -> None:
        """
        Download multiple YouTube videos and extract audio concurrently.

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
            future_to_url = {executor.submit(self.download_video_and_audio, url, cookies_file): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, message = future.result()
                    status = "Success" if success else "Failed"
                    logger.info(f"[{status}] {message}")
                except Exception as e:
                    logger.error(f"[Failed] Exception occurred while processing {url}: {e}")

        logger.info("Download session completed.")

    def run_ui(self) -> None:
        """
        User Interface function to handle user input and execute corresponding actions.
        """
        logger.info("\nWelcome to the YouTube Video and Audio Downloader")
        while True:
            print("\nSelect an option:")
            print("(1) Download a YouTube video and extract audio")
            print("(2) Download videos from urls.txt and extract audio")
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
                    success, message = self.download_video_and_audio(
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