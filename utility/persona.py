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
DEFAULT_IMAGE_FOLDER = "/Users/yuanlu/Desktop/test"

# Define your complex prompt here
ANALYSIS_PROMPT = """
You will be analyzing a social media influencer's persona based on a set of images. The goal is to provide a comprehensive understanding of the influencer's content strategy, target audience, and production quality across all provided images.

Please analyze the influencer's persona according to the following structure, addressing EACH point specifically:

A. 人设定位 (Persona Positioning)
A1. 视角 (Perspective)
A2. 粗分领域 (Broad Field)
A3. 细分领域 (Specific Field)
A4. 专业程度 (Level of Expertise)
A5. 自我标签 (Self-Labels)
A6. 语言特点 (Language Characteristics)
A7. 个人形象 (Personal Image)
A8. 情感倾向 / 价值观 (Emotional Tendency / Values)
A9. 审美 (Aesthetics)
A10. 叙事结构和故事性 (Narrative Structure and Storytelling)
A11. 布景／场地 (Setting / Location)

B. 目标受众 (Target Audience)
B1. 年龄 / 婚姻状况 (Age / Marital Status)
B2. 地域 (Geographic Location)
B3. 教育背景 / 职业 (Educational Background / Occupation)
B4. 经济状况 / 生活方式 (Economic Status / Lifestyle)
B5. 是否是特定群体 (Specific Group Affiliation)
B6. 目标受众的痛点 (Target Audience Pain Points)
B7. 博主与受众的互动性 (Influencer-Audience Interaction)
B8. 博主与受众是否有强粘性 (Influencer-Audience Stickiness)
B9. 视频播放量、点赞率、评论率 (Video Views, Like Rate, Comment Rate)

C. 内容制作专业度 (Content Production Professionalism)
C1. 视频长度 / 内容节奏 (Video Length / Content Pacing)
C2. 使用的特效和转场 (Special Effects and Transitions)
C3. 音乐选择和配音风格 (Music Selection and Voice-over Style)
C4. 一致性 / 系列化 (Consistency / Serialization)
C5. 热点敏感度 / 内容长青度 (Trend Sensitivity / Evergreen Content)
C6. 对独特性 / 原创性要求 (Uniqueness / Originality Requirements)
C7. 适合的品牌合作类型／潜在的达人合作机会 (Suitable Brand Collaborations / Potential Influencer Partnerships)
C8. 技术水平 (Technical Skill Level)
C9. SEO意识和推广策略 (SEO Awareness and Promotion Strategy)
C10. 潜在的负面影响和应对策略 (Potential Negative Impacts and Mitigation Strategies)

Provide your analysis in a structured format, using the section headers A, B, and C, and numbering each point as shown above (A1, A2, A3, etc.). Address EVERY point specifically. If any point cannot be determined from the given information, state so clearly for that specific point.

Begin your response with:
<analysis>

End your response with:
</analysis>

Remember to base your analysis on all provided images and avoid making assumptions beyond the given information. Ensure that you address each numbered point individually and comprehensively.
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
        'model': 'claude-3-sonnet-2024062',
        'max_tokens': 2000,
        'temperature': 0,
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
    # Use the DEFAULT_IMAGE_FOLDER as a default value, but allow it to be overridden
    image_folder = input(f"Enter the path to the image folder (press Enter to use default: {DEFAULT_IMAGE_FOLDER}): ").strip()
    if not image_folder:
        image_folder = DEFAULT_IMAGE_FOLDER

    folder_name = os.path.basename(image_folder)
    output_file = f"analysis_results_{folder_name}.txt"
    
    if not os.path.isdir(image_folder):
        logger.error(f"Error: The directory '{image_folder}' does not exist.")
        return

    try:
        analyze_images(image_folder, output_file)
    except Exception as e:
        logger.exception(f"An error occurred during image analysis: {str(e)}")

if __name__ == "__main__":
    main()
