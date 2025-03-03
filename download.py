import yt_dlp
import os
import re
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================
# TikTokDownloader Class
# ============================
class TikTokDownloader:
    def __init__(self, save_path: str = 'tiktok_videos'):
        """
        Initialize the downloader with a directory to save videos.
        """
        self.save_path = save_path
        self.create_save_directory()
    
    def create_save_directory(self) -> None:
        """Create the save directory if it doesn't exist."""
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if the provided URL is a TikTok URL.
        """
        tiktok_pattern = r'https?://((?:vm|vt|www|m)\.)?tiktok\.com/.*'
        return bool(re.match(tiktok_pattern, url))
    
    @staticmethod
    def progress_hook(d: Dict[str, Any]) -> None:
        """
        Hook to display download progress.
        """
        if d.get('status') == 'downloading':
            progress = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"Downloading: {progress} at {speed} ETA: {eta}", end='\r')
        elif d.get('status') == 'finished':
            print("\nDownload completed, finalizing...")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Remove invalid filename characters.
        """
        return re.sub(r'[\\/*?:"<>|]', "", filename)
    
    def get_metadata_based_filename(self, info: Dict[str, Any]) -> str:
        """
        Generate a filename based on the video's caption or title.
        """
        caption = info.get("description") or info.get("title")
        if caption:
            sanitized_caption = self.sanitize_filename(caption.strip())
            if len(sanitized_caption) > 100:
                sanitized_caption = sanitized_caption[:100].strip()
            return f"{sanitized_caption}.mp4"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"tiktok_{timestamp}.mp4"
    
    def get_filename(self, custom_name: Optional[str] = None) -> str:
        """
        Generate a filename with an optional custom name and a timestamp.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name:
            return f"{self.sanitize_filename(custom_name)}_{timestamp}.mp4"
        return f"tiktok_{timestamp}.mp4"
    
    def download_video(self, video_url: str, custom_name: Optional[str] = None) -> Optional[str]:
        """
        Download a TikTok video. If extraction fails with the desktop UA, a fallback
        mobile URL with a mobile user agent is tried.
        """
        if not self.validate_url(video_url):
            print(f"Error: Invalid TikTok URL: {video_url}")
            return None

        # Default extraction options with a desktop user agent.
        extraction_opts = {
            'quiet': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/91.0.4472.124 Safari/537.36'
                )
            }
        }
        info = None
        try:
            with yt_dlp.YoutubeDL(extraction_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
        except yt_dlp.utils.DownloadError as e:
            print(f"Extraction failed for {video_url}: {e}")
            # Try fallback: switch to mobile URL and user agent.
            if "www.tiktok.com" in video_url:
                mobile_url = video_url.replace("www.tiktok.com", "m.tiktok.com")
                print("Trying fallback mobile URL:", mobile_url)
                mobile_extraction_opts = extraction_opts.copy()
                mobile_extraction_opts['http_headers'] = {
                    'User-Agent': (
                        'Mozilla/5.0 (Linux; Android 10; SM-G970F) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/80.0.3987.119 Mobile Safari/537.36'
                    )
                }
                try:
                    with yt_dlp.YoutubeDL(mobile_extraction_opts) as ydl:
                        info = ydl.extract_info(mobile_url, download=False)
                    video_url = mobile_url  # use mobile URL for download
                except yt_dlp.utils.DownloadError as e2:
                    print(f"Fallback extraction failed for {mobile_url}: {e2}")
                    return None
            else:
                return None

        # Determine filename from metadata (or custom name)
        if custom_name is None:
            filename = self.get_metadata_based_filename(info)
        else:
            filename = self.get_filename(custom_name)
        output_path = os.path.join(self.save_path, filename)
        
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best',
            'noplaylist': True,
            'quiet': False,
            'progress_hooks': [self.progress_hook],
            'extractor_args': {'tiktok': {'webpage_download': True}},
            'http_headers': extraction_opts['http_headers']
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"\nVideo successfully downloaded: {output_path}")
            return output_path
        except yt_dlp.utils.DownloadError as e:
            print(f"Download error for {video_url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {video_url}: {e}")
        return None

# ============================
# Helper Functions
# ============================
def extract_valid_url(link: str) -> str:
    """
    Remove duplicated TikTok URL prefix if present.
    For example, convert:
      "https://www.tiktok.comhttps://www.tiktok.com/@thearabfooty/video/..."
    to:
      "https://www.tiktok.com/@thearabfooty/video/..."
    """
    duplicate_prefix = "https://www.tiktok.comhttps://www.tiktok.com"
    if duplicate_prefix in link:
        link = link.replace(duplicate_prefix, "https://www.tiktok.com", 1)
    return link

def load_video_links_from_json(file_path: str) -> List[str]:
    """
    Load video links from a JSON file with nested user data.
    Expected structure:
    {
        "users": {
            "username1": [link1, link2, ...],
            "username2": [link3, link4, ...]
        }
    }
    """
    video_links = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and "users" in data:
            for username, links in data["users"].items():
                if isinstance(links, list):
                    for link in links:
                        if isinstance(link, str):
                            fixed_link = extract_valid_url(link.strip())
                            video_links.append(fixed_link)
                else:
                    print(f"Expected a list of links for user {username} but got {type(links)}")
        else:
            print("JSON file structure is not recognized.")
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
    return video_links

def load_downloaded_links(filename: str = "downloaded_links.txt") -> set:
    """
    Load already downloaded video links from a log file.
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_downloaded_link(link: str, filename: str = "downloaded_links.txt") -> None:
    """
    Append a newly downloaded video link to the log file.
    """
    with open(filename, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# ============================
# Main Loop: 24/7 Video Downloader
# ============================
if __name__ == "__main__":
    json_file_path = 'tiktok_video_links.json'
    check_interval_seconds = 45 * 60  # 45 minutes

    # Load previously downloaded links from the log file.
    downloaded_links = load_downloaded_links()
    print("Loaded downloaded links:", downloaded_links)

    downloader = TikTokDownloader(save_path='downloaded_tiktoks')

    while True:
        print("\nChecking for new video links from JSON...")
        all_links = load_video_links_from_json(json_file_path)
        # Filter out any links that have already been downloaded.
        new_links = [link for link in all_links if link not in downloaded_links]

        if new_links:
            # Process each new video one-by-one.
            for video_link in new_links:
                print("Processing new video:", video_link)
                result = downloader.download_video(video_link)
                if result is not None:
                    downloaded_links.add(video_link)
                    save_downloaded_link(video_link)
                else:
                    print("Download failed for this video, skipping it.")
                print(f"Sleeping for {check_interval_seconds/60} minutes before the next video...")
                time.sleep(check_interval_seconds)
        else:
            print("No new video links found. Sleeping for 45 minutes...")
            time.sleep(check_interval_seconds)
