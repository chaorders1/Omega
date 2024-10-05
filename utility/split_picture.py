from PIL import Image
import os
import argparse

def get_output_format(input_file):
    # Get the file extension (format) of the input file
    _, ext = os.path.splitext(input_file)
    ext = ext.lower()

    # Map of common image extensions to PIL format strings
    format_map = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.tiff': 'TIFF'
    }

    # Return the format, defaulting to JPEG if unknown
    return format_map.get(ext, 'JPEG')

def split_picture(input_file, output_dir, part_height=1024):
    # Open the input image
    with Image.open(input_file) as img:
        # Get the dimensions of the image
        width, height = img.size
        
        # Calculate the number of parts
        num_parts = (height + part_height - 1) // part_height
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the output format
        output_format = get_output_format(input_file)
        
        # Get the appropriate file extension for the output format
        extension = '.jpg' if output_format == 'JPEG' else f'.{output_format.lower()}'
        
        # Split the image into parts
        for i in range(num_parts):
            top = i * part_height
            bottom = min((i + 1) * part_height, height)
            
            # Crop the image
            part = img.crop((0, top, width, bottom))
            
            # Save the part
            output_file = os.path.join(output_dir, f"part_{i+1}{extension}")
            part.save(output_file, output_format)
            print(f"Saved {output_file}")

def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_absolute_path(*relative_path):
    return os.path.join(get_project_root(), *relative_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split an image into multiple parts vertically.")
    parser.add_argument("--input_file", default="Data/picture/test.png", help="Path to the input image file")
    parser.add_argument("--output_dir", default="Data/split_output", help="Directory to save the split parts")
    parser.add_argument("--part_height", type=int, default=1024, help="Height of each part in pixels (default: 1024)")
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    input_file = get_absolute_path(args.input_file)
    output_dir = get_absolute_path(args.output_dir)

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        exit(1)

    split_picture(input_file, output_dir, args.part_height)