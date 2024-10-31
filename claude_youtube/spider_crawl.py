import os
from dotenv import load_dotenv
from spider import Spider
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the Spider with API key from environment variable
api_key = os.getenv('SPIDER_API_KEY')
if not api_key:
    raise ValueError('SPIDER_API_KEY environment variable is not set')

app = Spider(api_key=api_key)

def scrape_youtube_url(url: str) -> dict:
    """
    Scrape data from a YouTube URL with error handling.
    
    Args:
        url (str): YouTube URL to scrape
        
    Returns:
        dict: Scraped data or empty dict if error occurs
    """
    try:
        return app.scrape_url(url)
    except Exception as e:
        logger.error(f"Failed to scrape URL: {str(e)}")
        return {}

def save_to_markdown(data: dict, url: str) -> None:
    """
    Save scraped data to a markdown file with formatted content.
    
    Args:
        data (dict): Scraped data to save
        url (str): Original YouTube URL
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'youtube_data_{timestamp}.md'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('# YouTube Video Data\n\n')
            f.write(f'Source URL: {url}\n')
            f.write(f'Scraped at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            f.write('## Content\n\n')
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    f.write(f'### {key}\n')
                    f.write('```json\n')
                    f.write(json.dumps(value, indent=2))
                    f.write('\n```\n\n')
                else:
                    f.write(f'### {key}\n')
                    f.write(f'{value}\n\n')
        
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save data to markdown: {str(e)}")

# Scrape a single URL
url = 'https://www.youtube.com/watch?v=7kbQnLN2y_I'
scraped_data = scrape_youtube_url(url)

if scraped_data:
    logger.info("Successfully scraped data")
    save_to_markdown(scraped_data, url)
else:
    logger.warning("No data was scraped. Please check your API subscription/credits")