import yt_dlp
from pathlib import Path
from typing import Optional
import re
import unicodedata

# Pre-compiled regex patterns for filename sanitization
ILLEGAL_CHAR_PATTERN = re.compile(r'[^\w\s-]')
SPACE_PATTERN = re.compile(r'\s+')
YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.)?'
    r'(youtube\.com/watch\?v=|youtube\.[a-z]{2,3}/watch\?v=|youtu\.be/)'
    r'[^&\s]+$',
    re.IGNORECASE
)

def is_valid_youtube_url(url: str) -> bool:
    """Validate if the provided URL is a valid YouTube video URL."""
    return bool(YOUTUBE_URL_REGEX.match(url))

def sanitize_filename(title: str, max_length=255) -> str:
    """Sanitize a string to create a safe and clean filename."""
    sanitized_title = unicodedata.normalize('NFKD', title)
    sanitized_title = ILLEGAL_CHAR_PATTERN.sub('', sanitized_title)
    sanitized_title = SPACE_PATTERN.sub('_', sanitized_title).strip(".")
    sanitized_title = sanitized_title.encode('utf-8')[:max_length].decode('utf-8', 'ignore').rstrip('_')
    return unicodedata.normalize('NFC', sanitized_title)

def download_subtitles(
    video_url: str,
    output_dir: Path,
    cookies_file: Optional[Path] = None,
    lang: str = 'en',
    fmt: str = 'vtt',
    verbose: bool = False
) -> tuple:
    """
    Downloads subtitles for a YouTube video using yt-dlp.
    Tries to download manual subtitles; if not available, falls back to auto-generated subtitles.

    Args:
        video_url (str): The URL of the YouTube video.
        output_dir (Path): Directory where the subtitle file will be saved.
        cookies_file (Optional[Path]): Path to the cookies.txt file for authentication.
        lang (str): Subtitle language code (default: 'en').
        fmt (str): Subtitle format ('vtt' or 'srt').
        verbose (bool): Enable verbose output.

    Returns:
        tuple: (success (bool), message (str))
    """
    if not is_valid_youtube_url(video_url):
        return False, f"Invalid URL: {video_url}"

    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': fmt,
        'subtitleslangs': [lang],
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': not verbose,
        'no_warnings': not verbose,
        'cookiefile': str(cookies_file) if cookies_file else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            title = sanitize_filename(info_dict.get('title', 'video'))
            subtitle_file = output_dir / f"{title}.{fmt}"

            subtitles = info_dict.get('subtitles', {})
            auto_captions = info_dict.get('automatic_captions', {})
            available_langs = set(subtitles.keys()) | set(auto_captions.keys())

            if lang in subtitles:
                if verbose:
                    print(f"Manual subtitles found for language '{lang}', downloading...")
            elif lang in auto_captions:
                if verbose:
                    print(f"Auto-generated subtitles found for language '{lang}', downloading...")
            else:
                return False, f"No subtitles found for language '{lang}'."

            ydl.download([video_url])

            if verbose:
                print(f"Subtitles downloaded to {subtitle_file.resolve()}")

            return True, f"Downloaded subtitles for: {title}"

    except yt_dlp.utils.DownloadError as e:
        return False, f"Error downloading subtitles for {video_url}: {e}"

def download_subtitles_from_file(
    file_path: str,
    output_dir: Path,
    cookies_file: Optional[Path] = None,
    lang: str = 'en',
    fmt: str = 'vtt',
    verbose: bool = False
):
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

    print(f"Starting subtitle downloads for {len(valid_urls)} valid video URL(s)...")
    for index, url in enumerate(valid_urls, start=1):
        success, message = download_subtitles(
            url,
            output_dir,
            cookies_file=cookies_file,
            lang=lang,
            fmt=fmt,
            verbose=verbose
        )
        status = "Success" if success else "Failed"
        print(f"{index}. [{status}] {message}")

    print("Subtitle download session completed.")

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
        print("Proceeding without cookies. Note: Some subtitles may not download without authentication.")

    return None

def run_ui():
    """User Interface function to handle user input and execute corresponding actions."""
    print("\nWelcome to the YouTube Subtitle Downloader")
    while True:
        print("\nSelect an option:")
        print("(1) Download subtitles for a YouTube video")
        print("(2) Download subtitles for videos from urls.txt")
        print("(3) Quit")
        user_input = input("Enter 1, 2, or 3: ").strip().lower()

        if user_input == '3' or user_input == 'quit':
            print("Exiting the program. Goodbye!")
            break
        elif user_input == '2':
            file_path = Path.cwd() / "urls.txt"
            cookies_file = get_cookies_file()
            lang = input("Enter subtitle language code (e.g., 'en' for English): ").strip() or 'en'
            fmt = input("Enter subtitle format ('vtt' or 'srt'): ").strip().lower() or 'vtt'
            output_dir = Path(input("Enter output directory (default: 'Subtitles'): ").strip() or 'Subtitles')
            download_subtitles_from_file(
                str(file_path),
                output_dir,
                cookies_file=cookies_file,
                lang=lang,
                fmt=fmt
            )
        elif user_input == '1':
            video_url = input("Enter the YouTube video URL: ").strip()
            if is_valid_youtube_url(video_url):
                cookies_file = get_cookies_file()
                lang = input("Enter subtitle language code (e.g., 'en' for English): ").strip() or 'en'
                fmt = input("Enter subtitle format ('vtt' or 'srt'): ").strip().lower() or 'vtt'
                output_dir = Path(input("Enter output directory (default: 'Subtitles'): ").strip() or 'Subtitles')
                success, message = download_subtitles(
                    video_url,
                    output_dir,
                    cookies_file=cookies_file,
                    lang=lang,
                    fmt=fmt
                )
                print(message if success else f"Failed to download subtitles: {message}")
            else:
                print("Invalid URL. Please enter a valid YouTube video URL.")
        else:
            print("Invalid option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    run_ui()
