import os
from moviepy.editor import VideoFileClip

def extract_audio(video_path, output_format='mp3'):
    """
    Extract audio from a video file and save it in the Data directory.
    
    Args:
    video_path (str): Path to the input video file.
    output_format (str): Desired output audio format (default is 'mp3').
    
    Returns:
    str: Path to the extracted audio file.
    """
    try:
        # Get the video file name without extension
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Create the output folder in the Data directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), 'Data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Create output audio file path
        output_path = os.path.join(data_dir, f"{video_name}_audio.{output_format}")
        
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
