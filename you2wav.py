from pytube import YouTube
from pathlib import Path
import unicodedata
import subprocess
import re

# Configuration options
VERBOSE_FFMPEG = False  # Toggle True for verbose FFmpeg output

# Pre-ompiled regex patterns for filename sanitization
ILLEGAL_CHAR_PATTERN = re.compile(r'[^\w\s-]')

# Pre-compiled regex pattern to match any whitespace characters
SPACE_PATTERN = re.compile(r'\s+')

# Pre-compiled regex pattern to match a valid YouTube video URL
YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtube\.[a-z]{2,3}/watch\?v=|youtu\.be/)[^&\s]+$',
    re.IGNORECASE
)

# Global variable to cache the FFmpeg installation status
is_ffmpeg_installed_cache = None


def check_ffmpeg_installed():
    """Check if FFmpeg is installed and accessible in the system's PATH, using a cached result if available."""
    global is_ffmpeg_installed_cache

    # Return the cached result if the check has already been performed
    if is_ffmpeg_installed_cache is not None:
        return is_ffmpeg_installed_cache

    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        is_ffmpeg_installed_cache = True
        
    except subprocess.SubprocessError:
        print("FFmpeg is not installed or not found in PATH.")
        is_ffmpeg_installed_cache = False

    return is_ffmpeg_installed_cache


def is_valid_youtube_url(url: str) -> bool:
    """Validate if the provided URL is a valid YouTube video URL."""
    # Use the globally compiled regex for validation
    return bool(YOUTUBE_URL_REGEX.match(url))


def sanitize_filename(title: str, max_length=255) -> str:
    """
    Sanitize a string to create a safe and clean filename, considering maximum length.
    """
    # Normalizing, removing illegal characters, replacing spaces, and managing max_length
    sanitized_title = unicodedata.normalize('NFKD', title)
    sanitized_title = ILLEGAL_CHAR_PATTERN.sub('', sanitized_title)
    sanitized_title = SPACE_PATTERN.sub('_', sanitized_title).strip(".")
    # Encoding and slicing to handle max_length more accurately
    sanitized_title = sanitized_title.encode('utf-8')[:max_length].decode('utf-8', 'ignore').rstrip('_')
    return unicodedata.normalize('NFC', sanitized_title)


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


def run_ffmpeg_command(input_paths, output_path, options=None, verbose=False):
    """
    Run a FFmpeg command with given inputs, output, and options.

    Args:
        input_paths (list of str): Paths to input files.
        output_path (str): Path for the output file.
        options (list of str, optional): Additional options for FFmpeg command.
        verbose (bool): Flag to control the verbosity of FFmpeg output.

    Raises:
        subprocess.SubprocessError: If the FFmpeg command fails.
    """
    command = ['ffmpeg']

    # Add verbosity option
    command += ['-loglevel', 'verbose' if verbose else 'error']

    # Add input file(s) to command
    for path in input_paths:
        command += ['-i', path]

    # Add user-provided options
    if options:
        command += options

    # Add output file to command
    command += [output_path]

    # Execute the command
    subprocess.run(command, check=True)


def combine_streams(video_file_path, audio_file_path, output_path, verbose=False):
    """
    Combine video and audio streams into a single file using FFmpeg.

    Args:
        video_file_path: Path to the video file.
        audio_file_path: Path to the audio file.
        output_path: Output path for the combined file.
        verbose: Enable verbose FFmpeg output.
    """
    input_paths = [video_file_path, audio_file_path]
    # FFmpeg options to copy video codec and use AAC audio codec
    options = ['-c:v', 'copy', '-c:a', 'aac', '-y']
    run_ffmpeg_command(input_paths, output_path, options, verbose)


def convert_audio_to_wav(video_file_path, wav_path, verbose=False):
    """
    Extract the audio from the video file and convert it to WAV format using FFmpeg.

    Args:
        video_file_path: Path to the video file.
        wav_path: Output path for the WAV file.
        verbose: Enable verbose FFmpeg output.
    """
    input_paths = [video_file_path]
    # FFmpeg options to ignore video, use PCM signed 16-bit little endian audio codec, and set sample rate
    options = ['-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y']
    run_ffmpeg_command(input_paths, wav_path, options, verbose)


def download_and_process_video(video_url: str, folder_name: str = "Downloaded_Videos", verbose=False):
    """
    Coordinate the downloading and processing of YouTube videos.

    Args:
        video_url: URL of the YouTube video.
        folder_name: Name of the folder where videos will be downloaded.
    """
    if not check_ffmpeg_installed():
        return

    if not is_valid_youtube_url(video_url):
        print(f"Invalid video URL provided: {video_url}")
        return

    yt = YouTube(video_url)
    download_path = Path(folder_name).mkdir(parents=True, exist_ok=True)
    sanitized_title = sanitize_filename(yt.title)
    final_video_path = Path(folder_name) / f"{sanitized_title}.mp4"
    wav_path = Path(folder_name) / f"{sanitized_title}.wav"

    try:

        if yt.streams.filter(adaptive=True).first():
            video_file_path, audio_file_path = download_stream(yt, folder_name, 'adaptive')
            combine_streams(video_file_path, audio_file_path, str(final_video_path), verbose=verbose)

        else:
            download_stream(yt, folder_name, 'progressive')
        convert_audio_to_wav(str(final_video_path), str(wav_path), verbose=verbose)

        if verbose:
            print(f"Video saved in: '{final_video_path}'")
            print(f"Audio in WAV format saved in: '{wav_path}'")
        return True, f"Downloaded: {sanitized_title}"
    
    except Exception as e:
        return False, f"Error downloading {video_url}: {e}"


def download_videos_from_file(file_path: str, folder_name: str = "Downloaded_Videos", verbose=False):
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"'{file_path.name}' not found. Creating the file for you to add video URLs.")
        file_path.touch()
        return

    urls = file_path.read_text().splitlines()

    if not urls:
        print(f"'{file_path.name}' is empty. Please add some video URLs to it.")
        return

    valid_urls = [url for url in urls if is_valid_youtube_url(url)]

    if not valid_urls:
        print(f"No valid video URLs found in '{file_path.name}'.")
        return

    print(f"Starting downloads for {len(valid_urls)} valid video URL(s)...")

    for index, url in enumerate(valid_urls, start=1):
        success, message = download_and_process_video(url, folder_name, verbose=verbose)

        if success:
            print(f"{index}. {message}")

        else:
            print(f"{index}. {message} (Failed)")

    print("Download session completed.")


def run_ui():
    """
    User Interface function to handle user input and execute corresponding actions.
    """
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
            handle_file_download_option(file_path)

        elif user_input == '1':
            handle_single_video_download_option()

        else:
            print("Invalid option. Please enter 1, 2, or 3.")


def handle_file_download_option(file_path):

    if not file_path.exists():
        print(f"'{file_path.name}' not found. Creating the file for you to add video URLs.")
        file_path.touch()

    elif file_path.read_text().strip() == "":
        print("urls.txt is currently empty. Please add some YouTube URLs to it and try again.")

    else:
        download_videos_from_file(str(file_path), "Downloaded_Videos")


def handle_single_video_download_option():
    video_url = input("Enter the YouTube video URL: ").strip()

    if is_valid_youtube_url(video_url):
        success, message = download_and_process_video(video_url, "Downloaded_Videos")
        print(message if success else f"Failed to download: {message}")

    else:
        print("Invalid URL. Please enter a valid YouTube video URL.")


if __name__ == "__main__":
    run_ui()