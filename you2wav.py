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
    Sanitize a string to be safe for use as a filename by removing or replacing characters that are illegal or reserved in filenames.

    Args:
        title (str): The original video title that may contain invalid characters.

    Returns:
        str: A sanitized version of the title, safe to use as a filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title)

def check_ffmpeg_installed():
    """
    Checks if FFmpeg is installed and accessible in the system's PATH.

    Raises:
        RuntimeError: If FFmpeg is not found or an error occurs while checking.
    """
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("FFmpeg is installed and accessible.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("FFmpeg check failed. Please ensure FFmpeg is installed and added to your system's PATH.") from e
    except FileNotFoundError:
        raise RuntimeError("FFmpeg is not installed or not found in the system's PATH.")

def download_youtube_video(video_url:str, folder_name:str="Downloaded_Videos") -> None:
    """
    Downloads a YouTube video in the highest available quality, converts the audio to WAV format, and saves both video and audio files.

    Args:
        video_url (str): The URL of the YouTube video to download.
        folder_name (str, optional): The folder where the video and audio will be saved. Defaults to "Downloaded_Videos".
    """
    # First, check if FFmpeg is installed and accessible.
    check_ffmpeg_installed()
    # Create a directory path object for the download location.
    download_path = Path.cwd() / folder_name
    # Ensure the download directory exists, creating it if necessary.
    download_path.mkdir(parents=True, exist_ok=True)

    try:
        # Instantiate a YouTube object with the video URL to access video streams.
        yt = YouTube(video_url)
        # Fetch the highest quality non-progressive (video only) and audio streams.
        video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()
        audio_stream = yt.streams.get_audio_only()

        # Sanitize the video title to create valid filename.
        video_title = sanitize_filename(yt.title)
        # Define file paths for the video, audio, audio in WAV format, and the final combined video.
        video_path = download_path / f"{video_title}_video.mp4"
        audio_path = download_path / f"{video_title}_audio.mp4"
        wav_path = download_path / f"{video_title}.wav"
        final_path = download_path / f"{video_title}_final.mp4"

        if video_stream:
            # Download video and audio separately.
            print(f"Downloading video in {video_stream.resolution}")
            video_stream.download(output_path=str(download_path), filename=video_path.name)

            print("Downloading audio")
            audio_stream.download(output_path=str(download_path), filename=audio_path.name)

            # Combine video and audio files into one using FFmpeg.
            print("Combining video and audio")
            subprocess.run(['ffmpeg', '-i', str(video_path), '-i', str(audio_path), '-c:v', 'copy', '-c:a', 'aac', str(final_path), '-y'])

            # Convert downloaded audio to WAV format using FFmpeg.
            print("Converting audio to WAV format")
            subprocess.run(['ffmpeg', '-i', str(audio_path), str(wav_path), '-y'])

            print(f"Download completed! Combined video saved in: '{final_path}'")
            print(f"Audio converted to WAV and saved in: '{wav_path}'")
        else:
            # If no non-progressive video stream is found, attempt to download the best progressive stream available.
            progressive_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if progressive_stream:
                progressive_stream.download(output_path=str(download_path))
                print(f"Download completed! Progressive video saved in: '{download_path / video_title}.mp4'")
            else:
                print("No suitable streams found.")
    except Exception as e:
        # Handle exceptions and print the error message.
        print(f"An error occurred: {e}")

def download_videos_from_file(file_path: str, folder_name: str = "Downloaded_Videos"):
    """
    Downloads YouTube videos from a file containing a list of video URLs.
    """
    # Open and read the file containing YouTube URLs.
    with open(file_path, 'r') as file:
        urls = file.read().splitlines()  # Read all lines as a list of URLs.
        total_urls = len(urls)  # Count total URLs for user feedback.
        print(f"Found {total_urls} URLs in the file.")
        # Iterate over URLs and download each video.
        for index, url in enumerate(urls, start=1):
            print(f"Downloading video {index} of {total_urls}: {url}")
            try:
                download_youtube_video(url, folder_name)  # Attempt to download the video.
            except Exception as e:
                print(f"Failed to download {url}: {e}")  # Catch and report any errors.

def main():
    print("\nWelcome to the You2Wav Downloader")
    while True:  # Continuous loop until user decides to quit.
        # Prompt the user for their desired action.
        print("Select an option:")
        print("(1) Download a YouTube video")
        print("(2) Download videos from urls.txt")
        print("(3) Quit")
        user_input = input("Your choice (1, 2, or 3): ").strip().lower()

        # Process the user's input and perform the corresponding action.
        if user_input == '3' or user_input == 'quit':
            print("Exiting the program. Goodbye!")
            break  # Exit the loop and program.
        elif user_input == '2':
            # Check for the existence of urls.txt in the current directory.
            file_path = Path.cwd() / "urls.txt"
            if not file_path.exists():
                # Inform the user if urls.txt is missing and create an empty file.
                print("urls.txt not found in the current directory. Creating an empty urls.txt file.")
                file_path.touch()
                print("Please add YouTube URLs to urls.txt and run the option again.")
            else:
                # If urls.txt exists, proceed to download videos from it.
                download_videos_from_file(str(file_path))
        elif user_input == '1':
            # Prompt the user for a YouTube URL and download the video.
            video_url = input("Enter the YouTube video URL: ").strip()
            download_youtube_video(video_url)
        else:
            print("Invalid option. Please enter 1, 2, or 3.")  # Handle invalid input.

if __name__ == "__main__":
    main()  # Execute the main function if the script is run directly.