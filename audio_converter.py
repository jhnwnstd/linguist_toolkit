import yt_dlp
from pathlib import Path
import unicodedata
import re

# Configuration options
VERBOSE = False  # Toggle True for verbose output

# Pre-compiled regex patterns for filename sanitization
ILLEGAL_CHAR_PATTERN = re.compile(r'[^\w\s-]')
SPACE_PATTERN = re.compile(r'\s+')
YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtube\.[a-z]{2,3}/watch\?v=|youtu\.be/)[^&\s]+$',
    re.IGNORECASE
)

def is_valid_youtube_url(url: str) -> bool:
    """Validate if the provided URL is a valid YouTube video URL."""
    return bool(YOUTUBE_URL_REGEX.match(url))

def sanitize_filename(title: str, max_length=255) -> str:
    """Sanitize a string to create a safe and clean filename, considering maximum length."""
    sanitized_title = unicodedata.normalize('NFKD', title)
    sanitized_title = ILLEGAL_CHAR_PATTERN.sub('', sanitized_title)
    sanitized_title = SPACE_PATTERN.sub('_', sanitized_title).strip(".")
    sanitized_title = sanitized_title.encode('utf-8')[:max_length].decode('utf-8', 'ignore').rstrip('_')
    return unicodedata.normalize('NFC', sanitized_title)

def download_and_process_video(video_url: str, folder_name: str = "Downloaded_Videos_Audio", verbose=False, cookies_file=None):
    """
    Download a YouTube video using yt-dlp, merge streams if necessary,
    and extract audio to WAV format.
    """
    if not is_valid_youtube_url(video_url):
        return False, f"Invalid URL: {video_url}"

    download_path = Path(folder_name)
    download_path.mkdir(parents=True, exist_ok=True)

    # Prepare yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': str(download_path / '%(title)s.%(ext)s'),
        'quiet': not verbose,
        'no_warnings': not verbose,
        'cookiefile': str(cookies_file) if cookies_file else None,
        'merge_output_format': 'mp4',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            title = sanitize_filename(info_dict.get('title', 'video'))
            video_file = download_path / f"{title}.mp4"
            audio_file = download_path / f"{title}.wav"

            if verbose:
                print(f"Video saved to: '{video_file}'")
                print(f"Audio extracted to WAV format: '{audio_file}'")

            return True, f"Downloaded and processed: {title}"

    except yt_dlp.utils.DownloadError as e:
        return False, f"Error downloading {video_url}: {e}"

def download_videos_from_file(file_path: str, folder_name: str = "Downloaded_Videos_Audio", verbose=False, cookies_file=None):
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"'{file_path.name}' not found. Creating the file for you to add video URLs.")
        file_path.touch()
        return

    urls = file_path.read_text().splitlines()
    if not urls:
        print(f"'{file_path.name}' is empty. Please add some video URLs to it.")
        return

    valid_urls = [url.strip() for url in urls if is_valid_youtube_url(url.strip())]
    if not valid_urls:
        print(f"No valid video URLs found in '{file_path.name}'.")
        return

    print(f"Starting downloads for {len(valid_urls)} valid video URL(s)...")
    for index, url in enumerate(valid_urls, start=1):
        success, message = download_and_process_video(
            url, folder_name, verbose=verbose, cookies_file=cookies_file
        )
        status = "Success" if success else "Failed"
        print(f"{index}. [{status}] {message}")

    print("Download session completed.")

def get_cookies_file():
    """Prompt the user to provide the path to the cookies.txt file or use the default in the working directory."""
    default_cookies_path = Path.cwd() / "cookies.txt"
    if default_cookies_path.exists():
        use_default = input(f"Found 'cookies.txt' in the current directory. Use it? (y/n): ").strip().lower()
        if use_default == 'y':
            return default_cookies_path
    else:
        print("No 'cookies.txt' found in the current directory.")

    cookies_path = input("Enter the path to your 'cookies.txt' file (or press Enter to skip): ").strip()
    if cookies_path:
        cookies_file = Path(cookies_path)
        if cookies_file.exists():
            return cookies_file
        else:
            print(f"Cookies file '{cookies_file}' not found.")
    else:
        print("Proceeding without cookies. Note: Some videos may not download without authentication.")

    return None

def run_ui():
    """User Interface function to handle user input and execute corresponding actions."""
    print("\nWelcome to the You2Wav Downloader")
    while True:
        print("\nSelect an option:")
        print("(1) Download a YouTube video")
        print("(2) Download videos from urls.txt")
        print("(3) Quit")
        user_input = input("Enter 1, 2, or 3: ").strip().lower()

        if user_input == '3' or user_input == 'quit':
            print("Exiting the program. Goodbye!")
            break
        elif user_input == '2':
            file_path = Path.cwd() / "urls.txt"
            cookies_file = get_cookies_file()
            download_videos_from_file(str(file_path), "Downloaded_Videos_Audio", cookies_file=cookies_file)
        elif user_input == '1':
            video_url = input("Enter the YouTube video URL: ").strip()
            if is_valid_youtube_url(video_url):
                cookies_file = get_cookies_file()
                success, message = download_and_process_video(
                    video_url, "Downloaded_Videos_Audio", cookies_file=cookies_file
                )
                print(message if success else f"Failed to download: {message}")
            else:
                print("Invalid URL. Please enter a valid YouTube video URL.")
        else:
            print("Invalid option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    run_ui()