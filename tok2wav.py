import asyncio
import aiohttp
import re
import logging
from TikTokApi import TikTokApi
from pathlib import Path
import unicodedata

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for filename sanitization
ILLEGAL_CHAR_PATTERN = re.compile(r'[\\/*?:"<>|]')  # Matches any illegal filesystem characters
SPACE_PATTERN = re.compile(r'\s+')  # Matches any whitespace character

def is_valid_tiktok_url(url: str) -> bool:
    """Validate if the provided URL is a valid TikTok video URL."""
    pattern = re.compile(r'https?://(www\.)?tiktok\.com/@[^/]+/video/\d+(\?.*)?$')
    return bool(pattern.match(url))

def sanitize_filename(title: str, max_length=255) -> str:
    """Sanitize a string to create a safe and clean filename."""
    title = unicodedata.normalize('NFD', title).encode('ascii', 'ignore').decode('ascii')
    title = ILLEGAL_CHAR_PATTERN.sub('', title)
    title = SPACE_PATTERN.sub('_', title)
    return title[:max_length].rstrip("_")

async def download_video(session: aiohttp.ClientSession, url: str, path: Path):
    """Asynchronously download a video given its URL using an existing aiohttp session."""
    async with session.get(url) as response:
        if response.status == 200:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
            logger.info(f"Video downloaded successfully to {path}.")
        else:
            logger.error(f"Failed to download the video from {url}.")

async def download_tiktok_video(api: TikTokApi, session: aiohttp.ClientSession, video_url: str, download_folder: Path):
    """Download a TikTok video after validating its URL."""
    if not is_valid_tiktok_url(video_url):
        logger.error("Invalid TikTok URL provided.")
        return

    try:
        video_id = video_url.split('/')[-1]
        video_data = await api.video(id=video_id).info()
        video_title = video_data['itemInfo']['itemStruct']['desc']
        sanitized_title = sanitize_filename(video_title)
        video_download_url = video_data['itemInfo']['itemStruct']['video']['downloadAddr']
        download_path = download_folder / f"{sanitized_title}.mp4"
        await download_video(session, video_download_url, download_path)
    except Exception as e:
        logger.error(f"Error downloading TikTok video: {e}")

async def main():
    """Main function to handle user input and manage download tasks."""
    download_folder = Path("./downloaded_videos")

    # Create instances outside of 'async with' to manually manage their lifecycle
    api = TikTokApi()
    session = aiohttp.ClientSession()
    try:
        # Implementing batch download from a text file
        urls_file = Path("tiktok_urls.txt")
        if urls_file.exists():
            urls = urls_file.read_text().splitlines()
            for url in urls:
                if is_valid_tiktok_url(url):
                    await download_tiktok_video(api, session, url, download_folder)
                else:
                    logger.error(f"Invalid TikTok URL: {url}")
        else:
            logger.info("No urls.txt file found. Please create one with TikTok video URLs to download in batch.")
    finally:
        await session.close()
        # Manually invoke cleanup if needed, e.g., `await api.close_sessions()`
        # Avoid using `await api.__aexit__()`, which expects exception info as arguments

if __name__ == "__main__":
    asyncio.run(main())
