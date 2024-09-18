import os
import requests
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_filename(url):
    """Generate a short filename based on the URL hash."""
    return hashlib.md5(url.encode()).hexdigest()[:10] + '.mp4'

def download_video(video_url, output_folder):
    """
    Download a video from a given URL.
    
    Args:
    video_url (str): The URL of the video to download.
    output_folder (str): The folder where the video will be saved.
    
    Returns:
    str: The path to the downloaded video file, or None if download failed.
    """
    try:
        logger.info(f"Downloading video from URL: {video_url}")
        response = requests.get(video_url, stream=True)
        
        if response.status_code == 200:
            filename = generate_filename(video_url)
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            logger.info(f"Downloaded: {filename}")
            return filepath
        else:
            logger.error(f"Failed to download video: HTTP status code {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None

def batch_download_videos(video_urls, output_folder):
    """
    Batch download videos from a list of URLs.
    """
    os.makedirs(output_folder, exist_ok=True)

    logger.info(f"Found {len(video_urls)} videos. Starting download...")

    successful_downloads = 0
    for url in video_urls:
        if download_video(url, output_folder):
            successful_downloads += 1

    logger.info(f"Download completed. Successfully downloaded {successful_downloads} out of {len(video_urls)} videos.")

if __name__ == "__main__":
    video_urls_input = input("Enter the video URLs (separated by commas): ")
    video_urls = [url.strip() for url in video_urls_input.split(',')]
    output_folder = input("Enter the output folder path: ")
    
    batch_download_videos(video_urls, output_folder)
