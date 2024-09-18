"""
YouTube Transcript Fetcher

This module provides functionality to fetch and save transcripts from YouTube videos.
It supports both English and Simplified Chinese transcripts.

Dependencies:
- youtube_transcript_api
- pytube
"""

from typing import Dict, Optional, List, Union
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import re
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if not video_id_match:
        raise ValueError("Invalid YouTube URL")
    return video_id_match.group(1)

def get_video_title(url: str) -> str:
    """Fetch the title of a YouTube video."""
    try:
        return YouTube(url).title
    except Exception as e:
        logger.error(f"Error fetching video title: {e}")
        raise

def format_transcript_with_timestamps(transcript: List[Dict[str, Union[str, float]]]) -> str:
    """Format the transcript with timestamps."""
    return "\n".join(f"[{format_time(entry['start'])}] {entry['text']}" for entry in transcript)

def format_time(seconds: float) -> str:
    """Format time in seconds to HH:MM:SS format."""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_youtube_transcript(url: str) -> Optional[Dict[str, str]]:
    """Fetch the transcript of a YouTube video in any available language."""
    try:
        video_id = extract_video_id(url)
        video_title = get_video_title(url)
        
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Log available transcripts
        logger.info(f"Available transcripts: {[tr.language_code for tr in transcript_list]}")
        
        # Try to get transcript in any available language
        for transcript in transcript_list:
            try:
                formatted_transcript = format_transcript_with_timestamps(transcript.fetch())
                logger.info(f"Transcript found in language: {transcript.language_code}")
                return {
                    'transcript': formatted_transcript,
                    'title': video_title,
                    'language': transcript.language_code
                }
            except Exception as e:
                logger.warning(f"Failed to fetch transcript in {transcript.language_code}: {e}")
        
        logger.warning("No suitable transcript available for this video.")
        return None
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return None

def save_transcript_to_file(transcript_data: Dict[str, str], url: str) -> None:
    """Save the transcript to a file."""
    try:
        video_id = extract_video_id(url)
        video_title = transcript_data['title']
        language = transcript_data['language']

        data_dir = os.path.join(os.path.dirname(__file__), '..', 'Data')
        os.makedirs(data_dir, exist_ok=True)

        safe_title = re.sub(r'[^\w\-_\. ]', '_', video_title)
        filename = f"{safe_title}_{language}_transcript.txt"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(transcript_data['transcript'])

        logger.info(f"Transcript saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving transcript: {e}")
        raise

def main():
    """Main function to run the script."""
    try:
        youtube_url = input("Enter the YouTube video URL: ")
        transcript_data = get_youtube_transcript(youtube_url)
        if transcript_data:
            logger.info(f"Transcript retrieved successfully in {transcript_data['language']}.")
            save_transcript_to_file(transcript_data, youtube_url)
        else:
            logger.error("Failed to fetch transcript. Please check the logs for more details.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

