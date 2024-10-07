import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_douyin_video(video_url, output_folder):
    """
    Download a single video from Douyin given its URL.
    
    Args:
    video_url (str): The URL of the Douyin video to download.
    output_folder (str): The folder where the video will be saved.
    
    Returns:
    str: The path to the downloaded video file, or None if download failed.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info(f"Accessing video URL: {video_url}")
        driver.get(video_url)
        
        try:
            video_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            video_src = video_element.get_attribute('src')
        except TimeoutException:
            logger.error("Timeout waiting for video element to load")
            return None
        
        if not video_src:
            logger.error("Could not find video source")
            return None
        
        # Download the video
        response = requests.get(video_src, stream=True)
        if response.status_code == 200:
            video_id = video_url.split('/')[-1]
            filename = f"video_{video_id}.mp4"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            logger.info(f"Downloaded: {filename}")
            return filepath
        else:
            logger.error(f"Failed to download video: HTTP status code {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None
    
    finally:
        driver.quit()

if __name__ == "__main__":
    video_url = input("Enter the Douyin video URL: ")
    output_folder = input("Enter the output folder path: ")
    
    os.makedirs(output_folder, exist_ok=True)
    
    downloaded_file = download_douyin_video(video_url, output_folder)
    
    if downloaded_file:
        print(f"Video downloaded successfully: {downloaded_file}")
    else:
        print("Failed to download the video.")
