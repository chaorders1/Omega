# Using Anthropic API version: 2023-06-01
# Claude model: claude-3-5-sonnet-20240620
# Relevant parameters:
#   - max_tokens_to_sample: 2000
#   - temperature: 1.0
#   - top_p: Not specified in code
#   - top_k: Not specified in code

import os
import requests
import logging
import time
from typing import List, Dict, Any

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

# Get the path to the directory containing the current script (utility folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the parent directory, then into the Data folder
INPUT_DIRECTORY = os.path.join(os.path.dirname(current_dir), 'Data', 'test_txt')
OUTPUT_DIRECTORY = os.path.join(os.path.dirname(current_dir), 'Data', 'test_txt')

COMPARISON_PROMPT = """
这两个文件中有两位短视频博主的画像，请给出在A大项中两位博主的相似度的"人设相似度评分"0%为截然不同，100%为完全一致：A1项权重40%  A3 项权重20%  A5 项权重20%  A6权重10%  A8 项权重10%，其他Ａ项权重平均如果A大项评分小于70%可以忽略下一步。如果A大项评分大与70%请继续分析Ｂ和C大项的异同，并给出"值得模仿评分"(0%为无法模仿，100%为完全可以复制）

Here are the influencer analyses you will be comparing:

{{INFLUENCER_ANALYSES}}

Please provide your analysis using the following structure:

<analysis>
1. 人设相似度评分: [评分]%
   (详细说明各项权重的计算过程和结果)

2. 值得模仿评分: [如果适用，给出评分]%
   (如果A大项评分大于70%，分析B和C大项的异同，并解释评分理由)

3. 总结:
   (简要总结两位博主的主要相似点和差异，以及可能的模仿价值)
</analysis>

请确保您的分析基于提供的信息，客观公正，不要做出超出给定数据的假设。
"""

def read_analysis_files(directory: str) -> Dict[str, str]:
    """
    Read all .txt files in the specified directory.

    Args:
        directory (str): Path to the directory containing analysis files.

    Returns:
        Dict[str, str]: A dictionary with filenames as keys and file contents as values.
    """
    analyses = {}
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                analyses[filename] = f.read()
    return analyses

def compare_influencers(analyses: Dict[str, str], output_file: str) -> None:
    """
    Compare influencers using the Claude API and save the results.

    Args:
        analyses (Dict[str, str]): Dictionary of analysis contents.
        output_file (str): Path to save the comparison results.

    Raises:
        requests.RequestException: If there's an error communicating with the Claude API.
    """
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01'
    }
    
    influencer_analyses = "\n\n".join([f"Influencer {i+1} ({filename}):\n{content}" 
                                       for i, (filename, content) in enumerate(analyses.items())])
    
    data = {
        'model': 'claude-3-5-sonnet-20240620',
        'max_tokens': 2000,
        'temperature': 1.0,
        'messages': [
            {
                'role': 'user',
                'content': [{'type': 'text', 'text': COMPARISON_PROMPT.replace('{{INFLUENCER_ANALYSES}}', influencer_analyses)}]
            }
        ]
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(CLAUDE_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            comparison = result['content'][0]['text']
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Comparison of influencers:\n\n")
                f.write(comparison)
            
            logger.info(f"Comparison completed. Results saved to {output_file}")
            return
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Unable to complete comparison.")
                raise

def main():
    """
    Main function to run the influencer comparison process.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.normpath(os.path.join(script_dir, '..', INPUT_DIRECTORY))
    output_dir = os.path.normpath(os.path.join(script_dir, '..', OUTPUT_DIRECTORY))

    if not os.path.isdir(input_dir):
        logger.error(f"Error: The directory '{input_dir}' does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        analyses = read_analysis_files(input_dir)
        if not analyses:
            logger.error("No analysis files found in the input directory.")
            return

        influencer_names = "_vs_".join(os.path.splitext(os.path.basename(file))[0] for file in analyses)
        output_file = os.path.join(output_dir, f"comparison_{influencer_names}.txt")
        compare_influencers(analyses, output_file)
    except Exception as e:
        logger.exception(f"An error occurred during influencer comparison: {str(e)}")

if __name__ == "__main__":
    main()
