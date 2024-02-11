## Before running the script, make sure to install the required libraries using pip:
## pip install pytube

## Ensure that FFmpeg is installed on your system and added to the system's PATH environment variable.
## You can download FFmpeg from https://ffmpeg.org/download.html and follow the installation instructions for your operating system.

## You can downalod FFmpeg with chocolatey on Windows by running the following command in the terminal:
## choco upgrade all -y
## choco install ffmpeg

## You can download FFmpeg with Homebrew on macOS by running the following command in the terminal:
## brew update
## brew upgrade
## brew install ffmpeg

## You can download FFmpeg with apt on Ubuntu by running the following command in the terminal:
## sudo apt update && sudo apt upgrade
## sudo apt install ffmpeg

import re
from pytube import YouTube
from pathlib import Path
import subprocess  # For executing FFmpeg commands

def sanitize_filename(title:str) -> str:
    """
    Removes characters from video titles that are reserved in filenames.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title)

def check_ffmpeg_installed():
    """
    Verifies FFmpeg is installed and accessible in PATH.
    Raises an error if FFmpeg isn't found.
    """
    try:
        # Tries to run FFmpeg version command to check its presence.
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("FFmpeg is installed and accessible.")
    except subprocess.CalledProcessError:
        # Raises error if FFmpeg command fails indicating it might not be installed correctly.
        raise RuntimeError("FFmpeg check failed. Ensure it's installed and in your system's PATH.")
    except FileNotFoundError:
        # Raises error if FFmpeg executable is not found in PATH.
        raise RuntimeError("FFmpeg not installed or not in PATH.")

def is_valid_url(url: str) -> bool:
    # Validates YouTube URLs
    pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/).+$')
    return bool(pattern.match(url))

def download_youtube_video(video_url: str, folder_name: str = "Downloaded_Videos"):
    """
    Downloads the highest quality video and its audio, converts audio to WAV.
    """
    check_ffmpeg_installed()  # Ensures FFmpeg is installed before proceeding.
    if not is_valid_url(video_url):
        print(f"Invalid YouTube URL provided: {video_url}")
        return  # Exit the function if the URL is invalid.
    download_path = Path(folder_name)
    download_path.mkdir(parents=True, exist_ok=True)  # Creates the download directory if it doesn't exist.

    yt = YouTube(video_url)  # Initializes the YouTube object with the video URL.
    # Selects the highest quality video and audio streams available.
    video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()
    audio_stream = yt.streams.get_audio_only()

    # Sanitizes the video title to create a valid filename.
    video_title = sanitize_filename(yt.title)
    # Constructs file paths for the video, audio, and converted audio files.
    video_path = download_path / f"{video_title}_video.mp4"
    audio_path = download_path / f"{video_title}_audio.mp4"
    wav_path = download_path / f"{video_title}.wav"
    final_path = download_path / f"{video_title}_final.mp4"

    # Downloads video and audio streams.
    video_stream.download(output_path=str(download_path), filename=video_path.name)
    audio_stream.download(output_path=str(download_path), filename=audio_path.name)
    # Combines video and audio, then converts audio to WAV format.
    subprocess.run(['ffmpeg', '-i', str(video_path), '-i', str(audio_path), '-c:v', 'copy', '-c:a', 'aac', str(final_path), '-y'])
    subprocess.run(['ffmpeg', '-i', str(audio_path), str(wav_path), '-y'])

    print(f"Download completed! Video saved in: '{final_path}'")  # Notifies user of completion.

def download_videos_from_file(file_path: str, folder_name: str = "Downloaded_Videos"):
    """
    Checks if urls.txt exists, if not, creates it and prompts the user to add URLs.
    If the file exists but contains no URLs, notifies the user.
    If there are URLs, checks each for validity and downloads valid ones.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"'{file_path.name}' not found. Creating the file. Please add YouTube URLs to it.")
        file_path.touch()
        return
    
    urls = file_path.read_text().splitlines()
    valid_urls = [url for url in urls if is_valid_url(url)]

    if not urls:
        print(f"'{file_path.name}' exists but contains no URLs. Please add some.")
        return
    elif not valid_urls:
        print(f"No valid YouTube URLs found in '{file_path.name}'. Please check the URLs.")
        return

    print(f"Found {len(valid_urls)} valid YouTube URL(s) in '{file_path.name}'.")
    for index, url in enumerate(valid_urls, start=1):
        try:
            print(f"Downloading video {index} of {len(valid_urls)}: {url}")
            download_youtube_video(url, folder_name)
        except Exception as e:
            print(f"Failed to download {url}: {e}")

def main():
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
                exit()  # Quits the program after informing the user.
            else:
                urls = file_path.read_text().splitlines()
                if len(urls) == 0:
                    print("urls.txt is empty. Please add some YouTube URLs to it.")
                    exit()  # Quits the program if urls.txt is empty.
                download_videos_from_file(str(file_path))
        elif user_input == '1':
            video_url = input("Enter the YouTube video URL: ").strip()
            if is_valid_url(video_url):
                download_youtube_video(video_url, "Downloaded_Videos")
            else:
                print("Invalid URL. Please enter a valid YouTube video URL or type 'back' to return to the main menu.")
        else:
            print("Invalid option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()