from pytube import YouTube
from pathlib import Path
import unicodedata
import subprocess
import re

# Constants should be in uppercase
VERBOSE_FFMPEG = False  # Set to True for verbose FFmpeg messaging

# Pre-compile regular expressions outside of functions for efficiency
ILLEGAL_CHAR_PATTERN = re.compile(r'(?u)[^-\w\s]') # Matches any character that is not a word character, whitespace or hyphen
SPACE_PATTERN = re.compile(r'\s+')  # Matches any whitespace character

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and accessible in the system's PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg is not installed or not found in PATH.")
        return False


def is_valid_url(url: str) -> bool:
    """
    Validate if the provided URL is a valid YouTube video URL.

    Args:
        url: The URL to validate.

    Returns:
        True if the URL is a valid YouTube video URL, False otherwise.
    """
    pattern = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtube\.[a-z]{2,3}/watch\?v=|youtu\.be/)[^&\s]+$',
        re.IGNORECASE  # Handle case-insensitive matching
    )
    return bool(pattern.match(url))


def sanitize_filename(title: str, max_length=255,
                      illegal_char_regex=ILLEGAL_CHAR_PATTERN,
                      space_regex=SPACE_PATTERN) -> str:
    """
    Sanitize a string to create a safe and clean filename.

    Args:
        title: The original title to be sanitized.
        max_length: The maximum length of the sanitized filename.
        illegal_char_regex: Pre-compiled regex for illegal characters.
        space_regex: Pre-compiled regex for spaces.

    Returns:
        The sanitized, filesystem-safe filename.
    """
    title = unicodedata.normalize('NFD', title)
    title = illegal_char_regex.sub('', title)
    title = space_regex.sub('_', title)
    title = title.strip(".")
    title_bytes = title.encode('utf-8')[:max_length]
    title = title_bytes.decode('utf-8', 'ignore').rstrip('_')
    return unicodedata.normalize('NFC', title)


def download_stream(yt, download_path, stream_type='progressive'):
    """
    Download the specified type of stream for a YouTube video.

    Args:
        yt: YouTube object.
        download_path: Path where the video will be downloaded.
        stream_type: Type of stream to download ('adaptive' or 'progressive').
    """
    download_path = Path(download_path)
    if stream_type == 'adaptive':
        video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
        audio_stream = yt.streams.filter(only_audio=True).first()
        video_filename = f"{sanitize_filename(yt.title)}_video.mp4"
        audio_filename = f"{sanitize_filename(yt.title)}_audio.mp4"
        video_file_path = video_stream.download(output_path=str(download_path), filename=video_filename)
        audio_file_path = audio_stream.download(output_path=str(download_path), filename=audio_filename)
        return str(download_path / video_filename), str(download_path / audio_filename)
    else:
        progressive_stream = yt.streams.get_highest_resolution()
        filename = f"{sanitize_filename(yt.title)}.mp4"
        video_file_path = progressive_stream.download(output_path=str(download_path), filename=filename)
        return str(download_path / filename), None


def combine_streams(video_file_path, audio_file_path, output_path, verbose=False):
    """
    Combine video and audio streams into a single file using FFmpeg.

    Args:
        video_file_path: Path to the video file.
        audio_file_path: Path to the audio file.
        output_path: Output path for the combined file.
        verbose: Enable verbose FFmpeg output.
    """
    loglevel = 'verbose' if verbose else 'error'
    subprocess.run(['ffmpeg', '-loglevel', loglevel, '-i', video_file_path, '-i', audio_file_path, '-c:v', 'copy', '-c:a', 'aac', output_path, '-y'], check=True)


def convert_audio_to_wav(video_file_path, wav_path, verbose=False):
    """
    Extract the audio from the video file and convert it to WAV format using FFmpeg.

    Args:
        video_file_path: Path to the video file.
        wav_path: Output path for the WAV file.
        verbose: Enable verbose FFmpeg output.
    """
    loglevel = 'verbose' if verbose else 'error'
    subprocess.run(['ffmpeg', '-loglevel', loglevel, '-i', video_file_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', wav_path, '-y'], check=True)


def download_and_process_video(video_url: str, folder_name: str = "Downloaded_Videos"):
    """
    Coordinate the downloading and processing of YouTube videos.

    Args:
        video_url: URL of the YouTube video.
        folder_name: Name of the folder where videos will be downloaded.
    """
    if not check_ffmpeg_installed():
        return

    if not is_valid_url(video_url):
        print(f"Invalid video URL provided: {video_url}")
        return

    yt = YouTube(video_url)
    download_path = Path(folder_name)
    download_path.mkdir(parents=True, exist_ok=True)
    sanitized_title = sanitize_filename(yt.title)
    final_video_path = download_path / f"{sanitized_title}.mp4"
    wav_path = download_path / f"{sanitized_title}.wav"

    if yt.streams.filter(adaptive=True).first():
        video_file_path, audio_file_path = download_stream(yt, download_path, stream_type='adaptive')
        combine_streams(video_file_path, audio_file_path, str(final_video_path))
    else:
        video_file_path, _ = download_stream(yt, download_path, stream_type='progressive')

    convert_audio_to_wav(str(final_video_path), str(wav_path))
    print(f"Download completed! Video saved in: '{final_video_path}', Audio in WAV format saved in: '{wav_path}'")


def download_videos_from_file(file_path: str, folder_name: str = "Downloaded_Videos"):
    """
    Check if urls.txt exists and has valid video URLs.

    Args:
        file_path: Path to the file containing YouTube URLs.
        folder_name: Name of the folder where videos will be downloaded.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"'{file_path.name}' not found. Creating the file. Please add video URLs to it.")
        file_path.touch()
        return

    urls = file_path.read_text().splitlines()
    valid_urls = [url for url in urls if is_valid_url(url)]

    if not urls:
        print(f"'{file_path.name}' is created but empty. Please add some video URLs to it.")
        return
    elif not valid_urls:
        print(f"No valid video URLs found in '{file_path.name}'. Please check the URLs.")
        return

    print(f"Found {len(valid_urls)} valid video URL(s) in '{file_path.name}'. Starting downloads...")
    for index, url in enumerate(valid_urls, start=1):
        try:
            print(f"Downloading video {index} of {len(valid_urls)}: {url}")
            download_and_process_video(url, folder_name)
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            continue  # Proceeds to the next URL in case of error.

def main():
    """
    Main function to run the You2Wav Downloader.
    """
    print("\nWelcome to the You2Wav Downloader")
    while True:
        print("Select an option:")
        print("(1) Download a YouTube video")
        print("(2) Download videos from urls.txt")
        print("(3) Quit")
        user_input = input("Enter 1, 2, or 3: ").strip().lower()

        if user_input == '3' or user_input == 'quit':
            print("Exiting the program. Goodbye!")
            break
        elif user_input == '2':
            file_path = Path.cwd() / "urls.txt"
            if not file_path.exists() or file_path.read_text().strip() == "":
                print("urls.txt not found in the current directory or is empty. Creating an empty urls.txt file.")
                file_path.touch()
                print("Please add YouTube URLs to urls.txt and run the option again.")
                return
            else:
                urls = file_path.read_text().splitlines()
                if len(urls) == 0:
                    print("urls.txt is empty. Please add some YouTube URLs to it.")
                    return
                download_videos_from_file(str(file_path))
        elif user_input == '1':
            video_url = input("Enter the YouTube video URL: ").strip()
            if is_valid_url(video_url):
                download_and_process_video(video_url, "Downloaded_Videos")
            else:
                print("Invalid URL. Please enter a valid YouTube video URL or type 'back' to return to the main menu.")
        else:
            print("Invalid option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()