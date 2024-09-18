import subprocess
import os
import json
from datetime import timedelta

def extract_frames(video_path, output_fps=1):
    # ... (previous code remains unchanged)

    # Rename files to include timestamp
    for i in range(1, total_frames + 1):
        old_filename = f'{video_name}_{i:06d}.jpg'
        
        # Calculate timestamp and format it properly
        total_seconds = i / output_fps
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format timestamp without milliseconds, ensuring two digits for minutes and seconds
        timestamp = f"{hours}:{minutes:02d}:{seconds:02d}"
        new_filename = f'{video_name}_{timestamp}.jpg'
        
        old_path = os.path.join(output_folder, old_filename)
        new_path = os.path.join(output_folder, new_filename)
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"Renamed frame {i}/{total_frames}")
        else:
            print(f"Frame {i} not found, skipping...")

    print(f"Frame extraction completed. Output folder: {output_folder}")

# ... (rest of the code remains unchanged)