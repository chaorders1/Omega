import os
import whisper
from datetime import timedelta

def generate_srt(audio_path, output_path=None):
    """
    Generate an SRT file from an audio file using OpenAI's Whisper medium model.
    
    Args:
    audio_path (str): Path to the input audio file.
    output_path (str, optional): Path to save the output SRT file. If not provided,
                                 it will be saved in the same directory as the audio file.
    
    Returns:
    str: Path to the generated SRT file.
    """
    # Load the Whisper medium model
    model = whisper.load_model("medium")
    
    # Transcribe the audio
    result = model.transcribe(audio_path)
    
    # Generate SRT content
    srt_content = ""
    for i, segment in enumerate(result["segments"], start=1):
        start_time = timedelta(seconds=segment["start"])
        end_time = timedelta(seconds=segment["end"])
        text = segment["text"].strip()
        
        srt_content += f"{i}\n"
        srt_content += f"{format_timedelta(start_time)} --> {format_timedelta(end_time)}\n"
        srt_content += f"{text}\n\n"
    
    # Determine output path
    if output_path is None:
        audio_dir = os.path.dirname(audio_path)
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(audio_dir, f"{audio_name}.srt")
    
    # Write SRT content to file
    with open(output_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)
    
    return output_path

def format_timedelta(td):
    """Format timedelta object to SRT timestamp format."""
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

if __name__ == "__main__":
    audio_path = input("Enter the path to your audio file: ").strip("'\"")
    srt_path = generate_srt(audio_path)
    print(f"SRT file generated successfully: {srt_path}")
