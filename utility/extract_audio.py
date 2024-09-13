import os
from moviepy.editor import VideoFileClip

def extract_audio(video_path, output_format='mp3'):
    """
    Extract audio from a video file.
    
    Args:
    video_path (str): Path to the input video file.
    output_format (str): Desired output audio format (default is 'mp3').
    
    Returns:
    str: Path to the extracted audio file.
    """
    try:
        # Get the video file name without extension
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Create output audio file path
        output_path = f"{video_name}_audio.{output_format}"
        
        # Load the video file
        video = VideoFileClip(video_path)
        
        # Extract the audio
        audio = video.audio
        
        # Write the audio to a file
        audio.write_audiofile(output_path)
        
        # Close the video to release resources
        video.close()
        
        print(f"Audio extracted successfully: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        return None

if __name__ == "__main__":
    video_path = input("Enter the path to your video file: ").strip("'\"")
    output_format = input("Enter the desired output audio format (default is mp3): ") or 'mp3'
    
    extracted_audio_path = extract_audio(video_path, output_format)
    
    if extracted_audio_path:
        print(f"Audio extraction completed. Output file: {extracted_audio_path}")
    else:
        print("Audio extraction failed.")
