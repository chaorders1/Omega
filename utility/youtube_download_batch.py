# This code not work
import os
from pytube import YouTube
from typing import List

def download_video(url: str, output_path: str = '.') -> None:
    """Download a single YouTube video.

    Args:
        url (str): The URL of the YouTube video.
        output_path (str): The directory where the video will be saved.
    """
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download(output_path=output_path)
        print(f"Downloaded: {yt.title}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def batch_download_videos(urls: List[str], output_path: str = '.') -> None:
    """Download multiple YouTube videos.

    Args:
        urls (List[str]): A list of YouTube video URLs.
        output_path (str): The directory where the videos will be saved.
    """
    for url in urls:
        download_video(url, output_path)

if __name__ == '__main__':
    # Example usage
    video_urls = [
        'https://www.youtube.com/watch?v=BnSPTSBSEPI',
        'https://www.youtube.com/watch?v=WPD5a2sO3sw',
        # Add more URLs as needed
    ]
    output_directory = 'downloads'
    os.makedirs(output_directory, exist_ok=True)
    batch_download_videos(video_urls, output_directory)
