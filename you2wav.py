## Before running the script, make sure to install the required libraries using pip:
## pip install pytube
## pip install Pathlib

## Ensure that FFmpeg is installed on your system and added to the system's PATH environment variable.
## You can download FFmpeg from https://ffmpeg.org/download.html and follow the installation instructions for your operating system.

## You can downalod FFmpeg with chocolatey on Windows by running the following command in the terminal:
## choco install ffmpeg

## You can download FFmpeg with Homebrew on macOS by running the following command in the terminal:
## brew install ffmpeg

## You can download FFmpeg with apt on Ubuntu by running the following command in the terminal:
## sudo apt install ffmpeg

# Import necessary libraries
import re
from pytube import YouTube
from pathlib import Path
import subprocess  # For executing external commands, specifically FFmpeg

def sanitize_filename(title:str) -> str:
    """
    Sanitize a string to be safe for use as a filename by removing or replacing characters that are illegal or reserved in filenames.

    Args:
        title (str): The original video title that may contain invalid characters.

    Returns:
        str: A sanitized version of the title, safe to use as a filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title)

def download_youtube_video(video_url:str, folder_name:str="Downloaded_Videos") -> None:
    """
    Downloads a YouTube video in the highest available quality, converts the audio to WAV format, and saves both video and audio files.

    Args:
        video_url (str): The URL of the YouTube video to download.
        folder_name (str, optional): The folder where the video and audio will be saved. Defaults to "Downloaded_Videos".
    """
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

if __name__ == "__main__":
    # Prompt the user for the YouTube video URL and execute the download function.
    video_url = input("Enter the YouTube video URL: ")
    download_youtube_video(video_url)