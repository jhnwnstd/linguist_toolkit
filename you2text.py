from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.error import HTTPError, URLError

def list_available_languages(captions):
    """
    Lists all available languages for captions.
    
    Args:
        captions (CaptionQuery): Captions object from pytube.
    """
    print("Available languages for captions:")
    for lang_code in captions.lang_code_index.keys():
        print(f"{lang_code}: {captions[lang_code].name}")

def download_captions(video_url, preferred_language='en'):
    """
    Downloads and cleans captions for a YouTube video, handling exceptions.
    
    Args:
        video_url (str): URL of the YouTube video.
        preferred_language (str): Preferred language code for the captions (default is 'en').
    
    Returns:
        tuple: Cleaned caption text and the language code of the downloaded captions, or None if unavailable.
    """
    try:
        yt = YouTube(video_url)
        captions = yt.captions

        if not captions:
            print("No captions available for this video.")
            return None, None

        # List available languages
        list_available_languages(captions)

        # Attempt to fetch the preferred language; otherwise, select the first available one.
        caption = captions.get_by_language_code(preferred_language) or next(iter(captions.values()), None)
        if not caption:
            print(f"No captions available in the preferred language ({preferred_language}).")
            return None, None

        # Clean caption text
        caption_text = caption.generate_srt_captions()
        clean_text = BeautifulSoup(caption_text, "html.parser").text

        return clean_text, caption.code
    except VideoUnavailable:
        print(f"Video {video_url} is unavailable, skipping.")
    except (HTTPError, URLError) as e:
        print(f"Network error: {e.reason}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None, None

def save_captions(text, video_id, language_code, output_dir=Path.cwd()):
    """
    Saves the captions to a file in the specified directory.
    
    Args:
        text (str): The caption text.
        video_id (str): YouTube video ID.
        language_code (str): Language code of the captions.
        output_dir (Path): Directory to save the caption file.
    """
    filename = f"{video_id}_{language_code}_captions.srt"
    path = output_dir / filename
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Captions saved to {path}")

def main():
    video_url = input("Enter the YouTube video URL: ").strip()
    preferred_language = input("Enter the preferred language code for captions (leave blank for automatic selection): ").strip() or 'en'
    output_dir = input("Enter output directory (leave blank for current directory): ").strip() or Path.cwd()
    output_dir = Path(output_dir)  # Ensure this is a Path object
    
    text, language_code = download_captions(video_url, preferred_language)
    
    if text:
        video_id = YouTube(video_url).video_id
        save_captions(text, video_id, language_code, output_dir)
    else:
        print("Unable to download captions for this video.")

if __name__ == "__main__":
    main()
