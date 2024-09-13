from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

def get_youtube_transcript(url):
    try:
        # Extract video ID from the URL using regex
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if video_id_match:
            video_id = video_id_match.group(1)
        else:
            raise ValueError("Invalid YouTube URL")
        
        # Get available transcript languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Initialize variables to store transcripts
        zh_hans_transcript = None
        en_transcript = None
        
        # Check for Simplified Chinese transcript first, then English
        for transcript in transcript_list:
            if transcript.language_code == 'zh-Hans':
                zh_hans_transcript = transcript.fetch()
                break  # Stop searching if Chinese transcript is found
            elif transcript.language_code == 'en':
                en_transcript = transcript
        
        # If Chinese transcript is not found, use English if available
        if zh_hans_transcript:
            return {'zh-Hans': " ".join([entry['text'] for entry in zh_hans_transcript])}
        elif en_transcript:
            return {'en': " ".join([entry['text'] for entry in en_transcript.fetch()])}
        else:
            print("No Simplified Chinese or English transcripts available.")
            return None
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return None

def save_transcript_to_file(transcript, url):
    # Extract video ID from the URL
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    video_id = video_id_match.group(1) if video_id_match else 'unknown'

    # Determine the language
    lang = list(transcript.keys())[0]

    # Create a filename
    filename = f"{video_id}_{lang}_transcript.txt"

    # Save the transcript to a file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(transcript[lang])

    print(f"Transcript saved to {filename}")

if __name__ == "__main__":
    youtube_url = input("Enter the YouTube video URL: ")
    transcript = get_youtube_transcript(youtube_url)
    if transcript:
        print("Transcript retrieved successfully.")
        save_transcript_to_file(transcript, youtube_url)
    else:
        print("Failed to fetch transcript")

