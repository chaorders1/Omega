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
A. 人设定位
A1. 视角＋年龄性别＋定位: (约30字, 如第一视角＋中年女性＋真实生活, 第一视角＋年轻男性＋校园搞笑短剧, 第三视角＋年轻女性居多＋情感短剧)
A2. 粗分领域: (列出1-2个大类, 如美食, 旅行, 科技, 时尚, 教育, 情感, 游戏)
A3. 细分领域: (约20字, 如实用粤菜菜谱)
A4. 专业程度: (给出1-4分的评分及简单评价)
[1分：无专业性，分享生活点滴; 2分：低专业性，比如分享某几次相关经验; 3分：较高专业性，博主是业余专家; 4分：极高专业性，博主是领域业内权威]
A5. 自我标签: (列出4-5个, 如"宠妻达人", "育儿专家")
A6. 语言特点: (约20字, 如幽默, 严肃, 温馨, 搞笑)
A7. 个人形象: (约50字, 如温和, 真实, 接地气, 有亲和力)
A8. 情感倾向 / 价值观: (约50字, 如传递温暖、注重家庭互动, 或注重宏观，善于提炼)
A9. 叙事结构和故事性: (给出1-4分的评分)
[1分-无故事性,随手拍或分享生活; 2分-低故事性，教育观众或解释某些事物; 3分-一般故事性,很多视频都有故事内容; 4分-几乎全部视频都讲述故事]
A10. 审美: (约50字, 简单说明色彩搭配，构图方式，风格偏好)
A11. 主要布景／场地: (列出2-3个, 如室内家庭, 室内餐馆, 室内高铁)

B. 内容策略
B1. 高赞视频主题: (约100字, 总结点赞数高于一万的视频的主题和大概规律。特别注意心形符号旁的点赞率)
B2. 高赞视频如何击中受众痛点: (最多5点, 共约50字, 总结点赞数高于一万的视频为什么能吸引受众)
B3. 博主与受众的粘性: (约50字, 简单评论博主与受众是否有强粘性)

C. 受众画像
C1. 年龄/性别／婚姻状况: (约20字, 如２０－２５岁 单身女性)
C2. 地域: (列出1-2个主要地区, 如中国南方)
C3. 教育背景/ 职业: (列出2-3个主要类别, 如学生, 白领)
C4. 经济状况/ 生活方式: (约30字, 如中产, 喜欢户外运动)
C5. 特定群体或喜好/ 亚文化: (列出1-2个, 如骑行, 对战游戏, 波斯猫控)
C6. 受众痛点: (约50字, 受众最需要什么)
C7. 博主与受众的互动性: (提及是否包括互动元素如问答或挑战)

D. 制作专业度
D1. 拍摄环境和设备要求
D2. 内容创作技能要求
D3. 时间投入要求
D4. 个人经历和专业背景
D5. 更新频率和持续性

E. 总结
(约300字, 主要提炼人设及账户特点，最好加上视频中的例子，不需要提建议)
</analysis>

Remember to adhere strictly to the word count requirements and maintain consistent formatting throughout your analysis. Base your evaluation solely on the information provided in the influencer data. If certain information is not available or unclear, you may use phrases like "Based on the available information..." or "It appears that..." to indicate uncertainty.

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
