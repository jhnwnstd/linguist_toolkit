from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.error import HTTPError, URLError

def list_available_languages(captions):
    """
    Lists all available languages for captions.
    """
    print("Available languages for captions:")
    for lang_code, caption_obj in captions.items():
        print(f"{lang_code} ({caption_obj.name}): Auto-generated: {'yes' if 'a.' in lang_code else 'no'}")

def download_captions(video_url, preferred_language='en'):
    """
    Downloads and cleans captions for a YouTube video, updated to handle caption availability better
    and to avoid using deprecated methods.
    """
    try:
        print("Initializing YouTube object...")
        yt = YouTube(video_url)
        captions = yt.captions

        print("Captions:", captions)  # Directly print captions to debug

        if not captions:
            print("No captions available for this video.")
            return None, None

        # Listing available languages for debugging or user information
        list_available_languages(captions)

        print("Attempting to download captions...")
        # Attempt to fetch manual captions first using dictionary access
        caption_key = preferred_language
        caption = captions.get(caption_key)
        if caption is None:
            print(f"No manual captions available in the preferred language ({preferred_language}). Trying auto-generated captions.")
            # Attempt to fetch auto-generated captions
            caption_key = preferred_language + '.a'  # Adjust for auto-generated captions
            caption = captions.get(caption_key)
            if caption is None:
                print("No captions available in the preferred language, including auto-generated.")
                return None, None

        print("Generating caption text...")
        caption_text = caption.generate_srt_captions()
        clean_text = BeautifulSoup(caption_text, "html.parser").text

        print("Captions downloaded successfully.")
        return clean_text, caption.code.strip('.')
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
    output_dir = Path(output_dir)
    
    text, language_code = download_captions(video_url, preferred_language)
    
    if text:
        video_id = YouTube(video_url).video_id
        save_captions(text, video_id, language_code, output_dir)
    else:
        print("Unable to download captions for this video.")

if __name__ == "__main__":
    main()
