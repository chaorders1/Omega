import asyncio
import nest_asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
import json
import time
from pydantic import BaseModel, Field
import os

nest_asyncio.apply()

async def simple_crawl() -> None:
    """Perform a simple crawl and save the result to a file."""
    # Construct the path to the Data folder, which is parallel to the utility folder
    data_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data')
    os.makedirs(data_folder, exist_ok=True)
    file_path = os.path.join(data_folder, 'crawl_result.txt')
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url='https://mp.weixin.qq.com/s/mirwLofU0QYUTug8OCTYmw')
        with open(file_path, 'w') as file:
            file.write(result.markdown)
        print(f'Result saved to {file_path}')

def main() -> None:
    """Main function to run the simple crawl."""
    asyncio.run(simple_crawl())

if __name__ == '__main__':
    main()