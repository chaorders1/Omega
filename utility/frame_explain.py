import os
import json
import anthropic
import base64

# Initialize the Anthropic client with the API key from environment variable
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

def process_frame(image_path):
    """
    Process a single frame using Claude API.
    
    Args:
    image_path (str): Path to the image file.
    
    Returns:
    dict: Extracted information from the frame.
    """
    # Extract timestamp from filename
    timestamp = os.path.basename(image_path).split('_')[-1].split('.')[0]
    
    # Read the image file and encode to base64
    with open(image_path, "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')

    # Prepare the prompt for Claude
    prompt = f"""Analyze this image and provide the following information:
    1. Environment: Describe the setting or location.
    2. Action: Describe any actions or activities taking place.
    3. Goods: List any notable objects or items visible.
    4. Expression: Describe the facial expressions or emotions of any people.
    5. Transcript: If there's any text visible in the image, provide a transcript.

    Please format your response as a JSON object with keys: environment, action, goods, expression, and transcript.
    """

    # Call Claude API
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
                            "data": img_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    # Parse Claude's response
    try:
        result = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        result = {
            "environment": "Error parsing response",
            "action": "Error parsing response",
            "goods": "Error parsing response",
            "expression": "Error parsing response",
            "transcript": "Error parsing response"
        }

    # Add timestamp to the result
    result["timestamp"] = timestamp

    return result

def process_frames(input_folder, output_file):
    """
    Process all frames in a folder and write results to a text file.
    
    Args:
    input_folder (str): Path to the folder containing frame images.
    output_file (str): Path to the output text file.
    """
    results = []

    # Process each frame in the input folder
    for filename in sorted(os.listdir(input_folder)):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(input_folder, filename)
            print(f"Processing frame: {filename}")
            result = process_frame(image_path)
            results.append(result)

    # Write results to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"Environment: {result['environment']}\n")
            f.write(f"Action: {result['action']}\n")
            f.write(f"Goods: {result['goods']}\n")
            f.write(f"Expression: {result['expression']}\n")
            f.write(f"Transcript: {result['transcript']}\n")
            f.write("\n---\n\n")

    print(f"Processing complete. Results written to {output_file}")

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set your API key using:")
        print("export ANTHROPIC_API_KEY='your_api_key_here'")
        exit(1)

    # Set input_folder
    input_folder = "output_test2_fps1.0"

    # Extract video name from input folder
    video_name = input_folder.split('_')[1]  # Assumes format "output_videoname_fps1.0"

    # Set output_file based on video name
    output_file = f"{video_name}_frame_analysis.txt"

    # Ensure the input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        exit(1)

    # If output_file doesn't have a directory path, use the current directory
    if not os.path.dirname(output_file):
        output_file = os.path.join(os.getcwd(), output_file)

    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Processing frames from: {input_folder}")
    print(f"Writing output to: {output_file}")

    process_frames(input_folder, output_file)
