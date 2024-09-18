from scipy.io import wavfile
import noisereduce as nr
import os
from pydub import AudioSegment

def remove_background_noise(input_audio_path, output_audio_path=None):
    """
    Remove background noise from an audio file and save the cleaned audio.
    
    Args:
    input_audio_path (str): Path to the input audio file.
    output_audio_path (str, optional): Path to save the output audio file.
    
    Returns:
    str: Path to the cleaned audio file.
    """
    print(f"Processing audio file: {input_audio_path}")
    
    # Determine output path if not provided
    if output_audio_path is None:
        audio_dir = os.path.dirname(input_audio_path)
        audio_name = os.path.splitext(os.path.basename(input_audio_path))[0]
        output_audio_path = os.path.join(audio_dir, f"{audio_name}_cleaned.wav")
    
    # Convert input audio to WAV if it's not already
    if not input_audio_path.lower().endswith('.wav'):
        print("Converting audio to WAV format...")
        audio = AudioSegment.from_file(input_audio_path)
        temp_wav_path = input_audio_path + '.temp.wav'
        audio.export(temp_wav_path, format="wav")
    else:
        temp_wav_path = input_audio_path

    # Load data
    rate, data = wavfile.read(temp_wav_path)
    
    # Perform noise reduction
    print("Applying noise reduction...")
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    
    # Save the cleaned audio
    print(f"Saving cleaned audio to: {output_audio_path}")
    wavfile.write(output_audio_path, rate, reduced_noise)
    
    # Remove temporary WAV file if created
    if temp_wav_path != input_audio_path:
        os.remove(temp_wav_path)
    
    return output_audio_path

if __name__ == "__main__":
    input_file = input("Enter the path to your audio file: ").strip("'\"")
    cleaned_audio_path = remove_background_noise(input_file)
    print(f"Noise reduction complete. Output saved to: {cleaned_audio_path}")
