import os
import whisper
import torch
from datetime import timedelta

def generate_srt(audio_path, output_path=None, language=None):
    """
    Generate an SRT file from an audio file using OpenAI's Whisper large model.
    
    Args:
    audio_path (str): Path to the input audio file.
    output_path (str, optional): Path to save the output SRT file.
    language (str, optional): Language code (e.g., 'en' for English, 'zh' for Chinese).
    
    Returns:
    str: Path to the generated SRT file.
    """
    # Load the Whisper large model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("large", device=device)
    
    print(f"Transcribing audio using large model on {device}... This may take a while.")
    
    # Transcribe with more options
    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        verbose=True
    )
    
    print("Transcription complete. Generating SRT file...")
    
    # Generate SRT content with word-level timestamps
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
    language = input("Enter the language code (e.g., 'en' for English, 'zh' for Chinese), or press Enter to auto-detect: ").strip() or None
    srt_path = generate_srt(audio_path, language=language)
    print(f"SRT file generated successfully: {srt_path}")
