import asyncio
import nest_asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
import json
import time
from pydantic import BaseModel, Field
import os
import base64
from PIL import Image
import io

nest_asyncio.apply()

async def simple_crawl() -> None:
    """Perform a simple crawl, save the result to a file, and take a screenshot."""
    # Construct the path to the Data folder, which is parallel to the utility folder
    data_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data')
    os.makedirs(data_folder, exist_ok=True)
    file_path = os.path.join(data_folder, 'crawl_result.txt')
    screenshot_path = os.path.join(data_folder, 'screenshot.png')
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = 'https://mp.weixin.qq.com/s/mirwLofU0QYUTug8OCTYmw'
        wait_for = 'css:#content'  # Adjust this selector based on the actual content you want to wait for
        
        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            screenshot=True,
            wait_for=wait_for
        )
        
        if result.success:
            with open(file_path, 'w') as file:
                file.write(result.markdown)
            print(f'Result saved to {file_path}')
            
            # Decode and save the screenshot
            image_data = base64.b64decode(result.screenshot)
            with open(screenshot_path, 'wb') as image_file:
                image_file.write(image_data)
            print(f'Screenshot saved to {screenshot_path}')
        else:
            print("Crawl failed.")

def main() -> None:
    """Main function to run the simple crawl."""
    asyncio.run(simple_crawl())

if __name__ == '__main__':
    main()