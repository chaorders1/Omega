import os
import time
import logging
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'Data', 'web_snapshots')
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
SCROLL_PAUSE_TIME = 2
DEFAULT_MIN_SNAPSHOTS = 2
DEFAULT_MAX_SNAPSHOTS = 10
MAX_WORKERS = 5

def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename by removing invalid characters.

    Args:
        filename (str): The original filename.

    Returns:
        str: The sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def setup_webdriver() -> webdriver.Chrome:
    """
    Set up and return a Chrome WebDriver instance.

    Returns:
        webdriver.Chrome: An instance of Chrome WebDriver.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={MAX_WIDTH},{MAX_HEIGHT}")
    
    # Force light mode
    chrome_options.add_argument("--force-color-profile=srgb")
    chrome_options.add_argument("--force-device-scale-factor=1")
    
    # Disable dark mode
    chrome_options.add_experimental_option("prefs", {
        "browser.enabled_labs_experiments": ["force-color-profile@2"],
        "devtools.preferences.theme": "\"light\"",
    })
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def disable_dark_mode(driver: webdriver.Chrome) -> None:
    """
    Inject CSS to disable dark mode styles.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
    """
    script = """
    var style = document.createElement('style');
    style.type = 'text/css';
    style.innerHTML = '* { background-color: white !important; color: black !important; }';
    document.getElementsByTagName('head')[0].appendChild(style);
    """
    driver.execute_script(script)

def render_and_snapshot(url: str, output_dir: str, scroll_pause_time: float = SCROLL_PAUSE_TIME, 
                        min_snapshots: int = DEFAULT_MIN_SNAPSHOTS, max_snapshots: int = DEFAULT_MAX_SNAPSHOTS) -> None:
    """
    Render a webpage and take snapshots.

    Args:
        url (str): The URL of the webpage to render.
        output_dir (str): The directory to save snapshots.
        scroll_pause_time (float): Time to pause between scrolls.
        min_snapshots (int): Minimum number of snapshots to take.
        max_snapshots (int): Maximum number of snapshots to take.
    """
    driver = setup_webdriver()
    
    try:
        driver.set_window_size(MAX_WIDTH, MAX_HEIGHT)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        disable_dark_mode(driver)  # Add this line
        
        title = sanitize_filename(driver.title)
        folder_name = os.path.join(output_dir, title)
        os.makedirs(folder_name, exist_ok=True)

        total_height = get_total_height(driver)
        viewport_height = driver.execute_script("return window.innerHeight")

        logger.info(f"Processing: {url}")
        logger.info(f"Folder: {folder_name}")
        logger.info(f"Initial page height: {total_height}px, Viewport height: {viewport_height}px")

        num_snapshots = max(min(int(total_height / viewport_height) + 1, max_snapshots), min_snapshots)
        logger.info(f"Will take approximately {num_snapshots} snapshots")

        current_scroll = 0
        snapshot_count = 0

        while current_scroll < total_height and snapshot_count < max_snapshots:
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            time.sleep(scroll_pause_time)

            new_height = get_total_height(driver)
            if new_height > total_height:
                total_height = new_height
                logger.info(f"Page height increased to {total_height}px")

            save_snapshot(driver, folder_name, snapshot_count)

            snapshot_count += 1
            current_scroll += viewport_height

        logger.info(f"Saved {snapshot_count} snapshots in {folder_name}")

    except Exception as e:
        logger.error(f"An error occurred while processing {url}: {e}")

    finally:
        driver.quit()

def get_total_height(driver: webdriver.Chrome) -> int:
    """
    Get the total height of the webpage.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        int: The total height of the webpage.
    """
    return driver.execute_script("""
        return Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.offsetHeight,
            document.body.clientHeight,
            document.documentElement.clientHeight
        );
    """)

def save_snapshot(driver: webdriver.Chrome, folder_name: str, snapshot_count: int) -> None:
    """
    Save a snapshot of the current viewport.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        folder_name (str): The folder to save the snapshot.
        snapshot_count (int): The current snapshot count.
    """
    screenshot = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(screenshot))
    img.save(os.path.join(folder_name, f"snapshot_{snapshot_count + 1}.png"))
    logger.info(f"Saved snapshot {snapshot_count + 1}")

def process_urls_from_file(file_path: str) -> List[str]:
    """
    Process URLs from a file.

    Args:
        file_path (str): The path to the file containing URLs.

    Returns:
        List[str]: A list of URLs.
    """
    with open(file_path, 'r') as file:
        return [url.strip() for url in file if url.strip()]

def main() -> None:
    """
    Main function to run the web snapshot tool.
    """
    parser = argparse.ArgumentParser(description='Capture snapshots of webpages.')
    parser.add_argument('input_file', type=str, help='Path to the input file containing URLs')
    parser.add_argument('--min_snapshots', type=int, default=DEFAULT_MIN_SNAPSHOTS, help='Minimum number of snapshots to capture')
    parser.add_argument('--max_snapshots', type=int, default=DEFAULT_MAX_SNAPSHOTS, help='Maximum number of snapshots to capture')
    parser.add_argument('--scroll_pause_time', type=float, default=SCROLL_PAUSE_TIME, help='Time to pause between scrolls')
    args = parser.parse_args()

    urls = process_urls_from_file(args.input_file)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(render_and_snapshot, url, BASE_OUTPUT_DIR, args.scroll_pause_time, args.min_snapshots, args.max_snapshots): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                logger.error(f'{url} generated an exception: {exc}')

if __name__ == "__main__":
    main()