import os
import requests
import base64
import json
import logging
from PIL import Image
import io
from typing import List, Dict, Any
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY environment variable is not set")

CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
MAX_IMAGE_SIZE = 1.15  # megapixels
DEFAULT_IMAGE_FOLDER = os.environ.get('DEFAULT_IMAGE_FOLDER', os.path.join('Data', 'test_picture'))
OUTPUT_DIRECTORY = os.environ.get('OUTPUT_DIRECTORY', 'Data')

# Define your complex prompt here
ANALYSIS_PROMPT = """
You will be analyzing a social media influencer's short video content based on the provided information. Your task is to evaluate the influencer using a specific analysis framework. Your evaluation should be vivid, descriptive, and easy to understand. Pay close attention to the word count requirements in parentheses. Strictly follow the framework structure and maintain consistent formatting.

Here is the influencer data you will be analyzing:

<influencer_data>
{{INFLUENCER_DATA}}
</influencer_data>

Please provide your analysis using the following structure:

<analysis>
A. 人设定位 (Persona Positioning)
A1. 视角＋年龄性别＋定位: (Describe in about 30 characters, e.g., 第一视角＋中年女性＋真实生活, 第一视角＋年轻男性＋校园搞笑短剧, 第三视角＋年轻女性居多＋情感短剧)
A2. 粗分领域: (List 1-2 broad categories, e.g., 美食, 旅行, 科技, 时尚, 教育, 情感, 游戏)
A3. 细分领域: (Describe in about 20 characters, e.g., 实用粤菜菜谱)
A4. 专业程度: (Provide a score from 1-5 and a brief evaluation)
[1分：无专业性，纯分享生活; 2分：低专业性，博主有少量经验; 3分：有一定专业性，博主有很多经验; 4分：较高专业性，博主是业余专家; 5分：极高专业性，博主是领域权威]
A5. 自我标签: (List 4-5 self-labels, e.g., "宠妻达人", "育儿专家")
A6. 语言特点: (Describe in about 20 characters, e.g., 幽默, 严肃, 温馨, 搞笑)
A7. 个人形象: (Describe in about 50 characters, e.g., 温和, 真实, 接地气, 有亲和力)
A8. 情感倾向 / 价值观: (Describe in about 50 characters, e.g., 传递温暖、注重家庭互动, 或注重宏观，善于提炼)
A9. 叙事结构和故事性: (Provide a score from 1-5)
[1分-无故事性, 2分-差故事性, 3分-一般故事性, 4分-高故事性, 5分-每一个视频都讲述故事]
[If the score is 4 or above, analyze whether the stories have high conflict]
A10. 审美: (Describe color schemes, composition methods, and style preferences in about 50 characters)
A11. 主要布景／场地: (List 2-3 main settings, e.g., 室内家庭, 室内餐馆, 室内高铁)

B. 内容表现 (Content Performance)
B1. 高赞视频特点: (Summarize in about 100 characters, focusing on videos with over 10,000 likes. Pay special attention to the like rate next to the heart symbol)
B2. 高赞视频比例: (Estimate the proportion of videos with over 10,000 likes compared to total videos)
B3. 博主与受众的粘性: (Comment briefly in about 50 characters on whether there is strong stickiness between the influencer and the audience)

C. 目标受众 (Target Audience)
C1. 年龄/性别／婚姻状况: (Describe in about 20 characters, e.g., ２０－２５岁 单身女性)
C2. 地域: (List 1-2 main regions, e.g., 中国南方)
C3. 教育背景/ 职业: (List 2-3 main categories, e.g., 学生, 白领)
C4. 经济状况/ 生活方式: (Describe in about 30 characters, e.g., 中产, 喜欢户外运动)
C5. 特定群体或喜好/ 亚文化: (List 1-2 specific interests or subcultures, e.g., 骑行, 对战游戏, 波斯猫控)
C6. 受众痛点: (Describe in about 50 characters what the audience needs most)
C7. 博主与受众的互动性: (Mention if there are interactive elements like Q&As or challenges)

D. 总结 (Summary)
D1. [Provide a summary of approximately 500 characters, focusing on the influencer's persona and account characteristics. Include specific examples from the videos when possible. Do not provide recommendations.]

</analysis>

When providing scores or evaluations, always explain your reasoning before giving the actual score. This helps to justify your assessment and provides more context for the reader.

For the summary section, focus on synthesizing the key points from your analysis, highlighting the most distinctive aspects of the influencer's persona and content. Include specific examples from their videos to illustrate your points, but avoid making recommendations or suggestions for improvement.
"""

def resize_image(img: Image.Image, max_size: float = MAX_IMAGE_SIZE) -> Image.Image:
    """
    Resize an image if it exceeds the maximum size.

    Args:
        img (Image.Image): The image to resize.
        max_size (float): Maximum size in megapixels.

    Returns:
        Image.Image: Resized image if necessary, otherwise the original image.
    """
    width, height = img.size
    megapixels = (width * height) / 1_000_000

    if megapixels <= max_size:
        return img

    scale = (max_size / megapixels) ** 0.5
    new_width = int(width * scale)
    new_height = int(height * scale)

    return img.resize((new_width, new_height), Image.LANCZOS)

def encode_image(file_path: str) -> str:
    """
    Encode an image file to base64, resizing if necessary.

    Args:
        file_path (str): Path to the image file.

    Returns:
        str: Base64 encoded image data.

    Raises:
        IOError: If there's an error reading the image file.
        ValueError: If the image format is not supported.
    """
    try:
        with Image.open(file_path) as img:
            img = resize_image(img)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except IOError as e:
        logger.error(f"Error reading image file {file_path}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Unsupported image format for file {file_path}: {str(e)}")
        raise

def encode_images(image_folder: str) -> List[Dict[str, Any]]:
    """
    Encode all images in a folder.

    Args:
        image_folder (str): Path to the folder containing images.

    Returns:
        List[Dict[str, Any]]: List of encoded image objects.
    """
    encoded_images = []
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(image_folder, filename)
            try:
                encoded_image = encode_image(file_path)
                encoded_images.append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/jpeg',
                        'data': encoded_image
                    }
                })
                logger.info(f"Successfully encoded image: {filename}")
            except Exception as e:
                logger.error(f"Error encoding image {filename}: {str(e)}")
    return encoded_images

def analyze_images(image_folder: str, output_file: str) -> None:
    """
    Analyze images using the Claude API and save the results.

    Args:
        image_folder (str): Path to the folder containing images.
        output_file (str): Path to save the analysis results.

    Raises:
        ValueError: If no valid images are found in the folder.
        requests.RequestException: If there's an error communicating with the Claude API.
    """
    encoded_images = encode_images(image_folder)
    
    if not encoded_images:
        logger.error("No valid images found in the folder.")
        raise ValueError("No valid images found in the folder.")
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01'
    }
    
    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'max_tokens': 2000,
        'temperature': 1.0,
        #'top_k': 40,  # Added top_k parameter
        #'top_p': 0.95,  # Added top_p parameter
        'messages': [
            {
                'role': 'user',
                'content': encoded_images + [{'type': 'text', 'text': ANALYSIS_PROMPT}]
            }
        ]
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(CLAUDE_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            analysis = result['content'][0]['text']
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Analysis for images in {image_folder}:\n\n")
                f.write(analysis)
            
            logger.info(f"Analysis completed. Results saved to {output_file}")
            return
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Unable to complete analysis.")
                raise

def main():
    """
    Main function to run the image analysis process.
    """
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct default paths relative to the script's location
    default_image_folder = os.path.normpath(os.path.join(script_dir, '..', DEFAULT_IMAGE_FOLDER))
    default_output_dir = os.path.normpath(os.path.join(script_dir, '..', OUTPUT_DIRECTORY))

    # Prompt user for image folder, use default if no input is provided
    image_folder = input(f"Enter the path to the image folder (press Enter to use default: {default_image_folder}): ").strip()
    if not image_folder:
        image_folder = default_image_folder

    folder_name = os.path.basename(image_folder)
    output_file = os.path.join(default_output_dir, f"analysis_results_{folder_name}.txt")
    
    if not os.path.isdir(image_folder):
        logger.error(f"Error: The directory '{image_folder}' does not exist.")
        return

    # Ensure the output directory exists
    os.makedirs(default_output_dir, exist_ok=True)

    try:
        analyze_images(image_folder, output_file)
    except Exception as e:
        logger.exception(f"An error occurred during image analysis: {str(e)}")

if __name__ == "__main__":
    main()
