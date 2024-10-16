# Video Frame Extraction Utility
# 
# This script provides functionality to extract frames from a video file at a specified frame rate.
# It uses ffmpeg and ffprobe to process the video and extract information.
#
# Main components:
# 1. extract_frames(video_path, output_fps): Extracts frames from the given video at the specified fps
# 2. main(): Handles user input and calls extract_frames
#
# Usage: Run the script and follow the prompts to input video path and desired frame rate.

import subprocess
import os
import json
from datetime import timedelta

def extract_frames(video_path, output_fps=1):
    # Generate output folder name based on video filename
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Create the output folder in the Data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(script_dir), 'Data')
    output_folder = os.path.join(data_dir, f"output_{video_name}_fps{output_fps}")
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get video information using ffprobe
    probe_command = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    probe_result = subprocess.run(probe_command, capture_output=True, text=True)
    
    if probe_result.returncode != 0:
        print(f"Error: ffprobe command failed. Error output:")
        print(probe_result.stderr)
        return

    try:
        video_info = json.loads(probe_result.stdout)
    except json.JSONDecodeError:
        print("Error: Unable to parse ffprobe output. ffprobe output:")
        print(probe_result.stdout)
        return

    # Extract video properties
    try:
        duration = float(video_info['format']['duration'])
    except KeyError:
        print("Error: Unable to extract video duration. Video info:")
        print(json.dumps(video_info, indent=2))
        return

    total_frames = int(duration * output_fps)

    # FFmpeg command to extract frames
    ffmpeg_command = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'fps={output_fps},format=yuv420p',  # Add format filter
        '-q:v', '2',  # Quality setting (lower is better, 2-5 is good range)
        f'{output_folder}/{video_name}_%06d.jpg'
    ]

    # Run FFmpeg command
    subprocess.run(ffmpeg_command, check=True)

    # Rename files to include timestamp
    for i in range(1, total_frames + 1):
        old_filename = f'{video_name}_{i:06d}.jpg'
        timestamp = str(timedelta(seconds=i/output_fps)).rstrip('0').rstrip('.')
        new_filename = f'{video_name}_{timestamp}.jpg'
        
        old_path = os.path.join(output_folder, old_filename)
        new_path = os.path.join(output_folder, new_filename)
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"Renamed frame {i}/{total_frames}")
        else:
            print(f"Frame {i} not found, skipping...")

    print(f"Frame extraction completed. Output folder: {output_folder}")

def main():
    video_path = input("Enter the path to your video file: ").strip("'\"")  # Remove quotes if present
    output_fps = float(input("Enter the desired output frame rate (e.g., 1 for 1 frame per second): "))
    
    extract_frames(video_path, output_fps)

if __name__ == "__main__":
    main()
