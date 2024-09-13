import os
from moviepy.editor import VideoFileClip
from anthropic import Anthropic
import json
import logging
import base64
from PIL import Image
import io
import pytesseract
from datetime import timedelta

logging.basicConfig(level=logging.INFO)

os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'

def get_video_name(video_path):
    """Extract the video name without extension."""
    return os.path.splitext(os.path.basename(video_path))[0]

def extract_frames(video_path, interval=5):
    """Extract frames from the video at given interval and save them."""
    video_name = get_video_name(video_path)
    output_dir = f"{video_name}_extracted_frames"
    os.makedirs(output_dir, exist_ok=True)
    video = VideoFileClip(video_path)
    frames = []
    for t in range(0, int(video.duration), interval):
        frame = video.get_frame(t)
        frame_path = os.path.join(output_dir, f"{video_name}_frame_{t}.jpg")
        Image.fromarray(frame).save(frame_path)
        frames.append((frame_path, t))
    logging.info(f"Extracted {len(frames)} frames to {output_dir}")
    return frames

def extract_subtitles(image_path):
    """Extract subtitles from an image using OCR."""
    try:
        image = Image.open(image_path)
        width, height = image.size
        subtitle_region = image.crop((0, height * 2 // 3, width, height))
        text = pytesseract.image_to_string(subtitle_region, lang='chi_sim')
        return text.strip()
    except pytesseract.TesseractError as e:
        logging.error(f"OCR Error: {str(e)}")
        return f"[OCR Failed for {os.path.basename(image_path)}]"

def analyze_frames(frame_paths_and_times, client):
    """Analyze frames using Claude API and extract subtitles."""
    analyses = []
    subtitles = []
    subtitle_count = 1

    for frame_path, frame_time in frame_paths_and_times:
        try:
            with open(frame_path, "rb") as img_file:
                img_str = base64.b64encode(img_file.read()).decode()
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": img_str
                                }
                            },
                            {
                                "type": "text",
                                "text": "Describe this scene in detail, including characters, actions, and settings."
                            }
                        ]
                    }
                ]
            )
            analyses.append((frame_time, response.content))

            # Extract subtitles
            subtitle_text = extract_subtitles(frame_path)
            if subtitle_text:
                start_time = timedelta(seconds=frame_time)
                end_time = timedelta(seconds=frame_time + 5)  # Changed to 5-second intervals
                subtitle_entry = f"{subtitle_count}\n{start_time} --> {end_time}\n{subtitle_text}\n\n"
                subtitles.append(subtitle_entry)
                subtitle_count += 1
        except Exception as e:
            logging.error(f"Error processing frame {frame_path}: {str(e)}")

    # Save subtitles to SRT file
    video_name = get_video_name(frame_paths_and_times[0][0])
    srt_path = f"{video_name}_extracted_subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.writelines(subtitles)
    
    logging.info(f"Extracted subtitles saved to {srt_path}")
    return analyses, srt_path

def generate_script(analyses, srt_path, client):
    """Generate a standard script using Claude API."""
    analyses_str = [str(analysis) for analysis in analyses]
    
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        subtitles = srt_file.read()
    
    prompt = f"""
    Based on the following scene analyses and subtitles in Chinese, generate a standard movie script in Chinese.
    Scene Analyses: {json.dumps(analyses_str)}
    Subtitles: {subtitles}
    
    Format the script according to standard Chinese screenplay format, including:
    1. Scene headings (INT/EXT, location, time of day)
    2. Action lines describing what's happening in the scene
    3. Character names before their dialogue
    4. Dialogue
    5. Parentheticals for brief descriptions of how a line is delivered
    
    Ensure the script flows naturally and captures the essence of the video content. The entire script should be in Chinese.
    """
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text if isinstance(response.content, list) else response.content

def main(video_path, output_path):
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        client = Anthropic(api_key=api_key)
        
        logging.info("Extracting frames...")
        frame_paths_and_times = extract_frames(video_path)
        
        logging.info("Analyzing frames and extracting subtitles...")
        analyses, srt_path = analyze_frames(frame_paths_and_times, client)
        
        logging.info("Generating script...")
        script = generate_script(analyses, srt_path, client)
        
        logging.info(f"Script type: {type(script)}")
        logging.info(f"Script length: {len(script)} characters")
        logging.info(f"Script beginning (first 500 characters):\n{script[:500]}")
        logging.info(f"Script ending (last 500 characters):\n{script[-500:]}")
        
        logging.info(f"Writing script to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        logging.info("Script generation complete!")
    except ValueError as ve:
        logging.error(f"Configuration error: {str(ve)}")
    except FileNotFoundError as fnf:
        logging.error(f"File not found: {str(fnf)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        logging.error(f"Error type: {type(e)}")
        logging.error(f"Error args: {e.args}")

if __name__ == "__main__":
    video_path = "beida_laosun.mp4"
    output_path = f"{get_video_name(video_path)}_output_script.txt"
    main(video_path, output_path)