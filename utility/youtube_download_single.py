import os
import youtube_dl
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Remove invalid characters from filename."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)

def download_youtube_video(url: str) -> None:
    # Set the output path to the Data directory
    output_path = os.path.join(os.path.dirname(__file__), '..', 'Data')
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'verbose': True,
        'ignoreerrors': True,  # Skip unavailable videos in a playlist
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Get video info
            info_dict = ydl.extract_info(url, download=False)
            if info_dict is None:
                logger.error("Failed to extract video information.")
                return
            
            if 'entries' in info_dict:
                # It's a playlist or a list of videos
                video_info = info_dict['entries'][0]
            else:
                # Just a single video
                video_info = info_dict
            
            video_title = video_info.get('title', None)
            
            if video_title:
                safe_title = sanitize_filename(video_title)
                ydl_opts['outtmpl'] = os.path.join(output_path, f'{safe_title}.%(ext)s')
            
            logger.info(f"Downloading: {video_title}")
            
            # Download the video
            ydl.download([url])
            
            logger.info(f"Download completed: {video_title}")
            logger.info(f"File saved in: {output_path}")
    except youtube_dl.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

def main():
    url = input("Enter the YouTube video URL: ")
    download_youtube_video(url)

if __name__ == "__main__":
    main()
