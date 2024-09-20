import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIRECTORY = os.path.join(os.path.dirname(SCRIPT_DIR), 'Data', 'web_snapshots')
MAX_WIDTH = 1920  # Maximum width for snapshots
MAX_HEIGHT = 1080  # Maximum height for each snapshot
SCROLL_PAUSE_TIME = 2
MIN_SNAPSHOTS = 5
MAX_SCROLL_ATTEMPTS = 20

def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={MAX_WIDTH},{MAX_HEIGHT}")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def wait_for_page_load(driver, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)  # Additional wait for any JavaScript rendering
    except Exception as e:
        logger.warning(f"Timeout waiting for page load: {e}")

def get_page_height(driver):
    return driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")

def scroll_and_capture(driver, url, output_folder):
    driver.get(url)
    wait_for_page_load(driver)

    total_height = get_page_height(driver)
    viewport_height = driver.execute_script("return window.innerHeight")
    
    snapshots = []
    scroll_position = 0
    scroll_attempts = 0

    while len(snapshots) < MIN_SNAPSHOTS and scroll_attempts < MAX_SCROLL_ATTEMPTS:
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(SCROLL_PAUSE_TIME)

        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        
        # Crop the image to remove any overlap
        crop_height = min(viewport_height, total_height - scroll_position)
        cropped_image = image.crop((0, 0, MAX_WIDTH, crop_height))
        
        snapshots.append(cropped_image)
        logger.info(f"Captured snapshot {len(snapshots)}")

        scroll_position += viewport_height
        scroll_attempts += 1

        # Check if we've reached the bottom of the page
        if scroll_position >= total_height:
            break

        # Update total height as it might have changed due to dynamic loading
        total_height = get_page_height(driver)

    return snapshots

def save_snapshots(snapshots, output_folder):
    for i, snapshot in enumerate(snapshots, 1):
        output_path = os.path.join(output_folder, f"snapshot_{i}.png")
        snapshot.save(output_path)
        logger.info(f"Saved snapshot {i} to {output_path}")

def main():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    url = input("Enter the URL of the website to snapshot: ")
    
    driver = setup_webdriver()
    try:
        output_folder = os.path.join(OUTPUT_DIRECTORY, url.split("//")[-1].split("/")[0])
        os.makedirs(output_folder, exist_ok=True)
        
        snapshots = scroll_and_capture(driver, url, output_folder)
        save_snapshots(snapshots, output_folder)
        
        logger.info(f"All snapshots saved in {output_folder}")
    except Exception as e:
        logger.exception(f"An error occurred during web snapshot: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()