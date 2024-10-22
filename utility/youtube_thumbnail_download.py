import os
from typing import Optional
from pythumb import Thumbnail
from urllib.parse import urlparse, parse_qs

def get_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.

    Args:
        url (str): The YouTube video URL.

    Returns:
        Optional[str]: The video ID if found, None otherwise.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        if parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    return None

def download_youtube_thumbnail(url: str, output_dir: str = 'thumbnails') -> Optional[str]:
    """
    Download the thumbnail of a YouTube video given its URL using pythumb.

    Args:
        url (str): The YouTube video URL.
        output_dir (str): The directory to save the thumbnail. Defaults to 'thumbnails'.

    Returns:
        Optional[str]: The path to the downloaded thumbnail if successful, None otherwise.
    """
    try:
        # Extract video ID
        video_id = get_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Create a Thumbnail object
        thumb = Thumbnail(url)
        
        # Fetch the thumbnail data
        thumb.fetch()
        
        # Construct the output path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        data_dir = os.path.join(project_root, 'Data')
        full_output_dir = os.path.join(data_dir, output_dir)
        
        # Ensure the output directory exists
        os.makedirs(full_output_dir, exist_ok=True)
        
        # Save the thumbnail with a custom filename
        output_filename = f"{video_id}.jpg"
        output_path = os.path.join(full_output_dir, output_filename)
        thumb.save(output_path)
        
        print(f"Thumbnail downloaded successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
        return None

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python youtube_thumbnail_download.py <youtube_url>")
        sys.exit(1)

    youtube_url = ' '.join(sys.argv[1:])  # Join all arguments to handle URLs with spaces
    download_youtube_thumbnail(youtube_url)
