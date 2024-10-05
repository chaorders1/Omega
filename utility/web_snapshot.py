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
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache
from urllib.parse import urlparse
from collections import defaultdict
import random
from ratelimit import limits, sleep_and_retry, RateLimitException

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
MAX_WORKERS = 10
MAX_RETRIES = 3
TIMEOUT = 30
DEFAULT_RATE_LIMIT = 30  # increased from 10 to 30
RATE_LIMIT_PERIOD = 60  # seconds
MIN_DELAY = 0.5  # reduced from 1 to 0.5
MAX_DELAY = 3  # reduced from 5 to 3

class AdaptiveRateLimiter:
    def __init__(self, default_limit=DEFAULT_RATE_LIMIT):
        self.domain_limits = defaultdict(lambda: default_limit)
        self.success_counts = defaultdict(int)
        self.failure_counts = defaultdict(int)

    def get_limit(self, domain):
        return self.domain_limits[domain]

    def update_limit(self, domain, success):
        if success:
            self.success_counts[domain] += 1
            if self.success_counts[domain] > 10:
                self.domain_limits[domain] = min(self.domain_limits[domain] * 1.1, 60)
                self.success_counts[domain] = 0
        else:
            self.failure_counts[domain] += 1
            if self.failure_counts[domain] > 2:
                self.domain_limits[domain] = max(self.domain_limits[domain] * 0.5, 10)
                self.failure_counts[domain] = 0

rate_limiter = AdaptiveRateLimiter()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename by removing invalid characters.

    Args:
        filename (str): The original filename.

    Returns:
        str: The sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@lru_cache(maxsize=1)
def get_chromedriver_path():
    """
    Get and cache the ChromeDriver path.

    Returns:
        str: Path to the ChromeDriver executable.
    """
    return ChromeDriverManager().install()

def setup_webdriver() -> webdriver.Chrome:
    """
    Set up and return a Chrome WebDriver instance with cached ChromeDriver path.

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
    
    service = Service(get_chromedriver_path())
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

def rate_limited_request(url, method='head'):
    domain = urlparse(url).netloc
    limit = rate_limiter.get_limit(domain)

    @sleep_and_retry
    @limits(calls=limit, period=RATE_LIMIT_PERIOD)
    def do_request():
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        if method == 'head':
            return requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        else:
            return requests.get(url, timeout=TIMEOUT, allow_redirects=True)

    try:
        response = do_request()
        rate_limiter.update_limit(domain, True)
        return response
    except RateLimitException:
        rate_limiter.update_limit(domain, False)
        raise

def check_url_accessibility(url: str) -> bool:
    """
    Check if the URL is accessible with adaptive rate limiting.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is accessible, False otherwise.
    """
    try:
        # First, try with a HEAD request
        response = rate_limited_request(url, method='head')
        if response.status_code == 200:
            return True
        
        # If HEAD request fails, try with a GET request
        if response.status_code in [403, 405]:  # Forbidden or Method Not Allowed
            response = rate_limited_request(url, method='get')
            return response.status_code == 200

        return False
    except (RequestException, RateLimitException):
        return False

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
def render_and_snapshot(url: str, output_dir: str, scroll_pause_time: float = SCROLL_PAUSE_TIME, 
                        min_snapshots: int = DEFAULT_MIN_SNAPSHOTS, max_snapshots: int = DEFAULT_MAX_SNAPSHOTS) -> None:
    """
    Render a webpage and take snapshots with improved efficiency and rate limiting.

    Args:
        url (str): The URL of the webpage to render.
        output_dir (str): The directory to save snapshots.
        scroll_pause_time (float): Time to pause between scrolls.
        min_snapshots (int): Minimum number of snapshots to take.
        max_snapshots (int): Maximum number of snapshots to take.
    """
    driver = setup_webdriver()
    
    try:
        # Add a random delay before loading the page
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        driver.set_window_size(MAX_WIDTH, MAX_HEIGHT)
        driver.set_page_load_timeout(TIMEOUT)
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for JavaScript content to load
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        disable_dark_mode(driver)
        
        title = sanitize_filename(driver.title)
        folder_name = os.path.join(output_dir, title)
        os.makedirs(folder_name, exist_ok=True)

        viewport_height = driver.execute_script("return window.innerHeight")
        total_height = get_total_height(driver)

        logger.info(f"Processing: {url}")
        logger.info(f"Folder: {folder_name}")
        logger.info(f"Initial page height: {total_height}px, Viewport height: {viewport_height}px")

        snapshot_count = scroll_and_capture(driver, folder_name, viewport_height, total_height,
                                            scroll_pause_time, max_snapshots)

        logger.info(f"Saved {snapshot_count} snapshots in {folder_name}")

    except Exception as e:
        logger.error(f"An error occurred while processing {url}: {e}")
        raise
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
    Save a snapshot of the current viewport as a PNG file.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        folder_name (str): The folder to save the snapshot.
        snapshot_count (int): The current snapshot count.
    """
    screenshot = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(screenshot))
    img = img.convert('RGB')  # Convert to RGB to ensure compatibility
    file_path = os.path.join(folder_name, f"snapshot_{snapshot_count + 1}.png")
    img.save(file_path, 'PNG')
    logger.info(f"Saved snapshot {snapshot_count + 1} to {file_path}")

def scroll_and_capture(driver: webdriver.Chrome, folder_name: str, viewport_height: int, total_height: int,
                       scroll_pause_time: float, max_snapshots: int) -> int:
    """
    Scroll the page and capture snapshots with lazy loading handling.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        folder_name (str): The folder to save snapshots.
        viewport_height (int): Height of the viewport.
        total_height (int): Total height of the page.
        scroll_pause_time (float): Time to pause between scrolls.
        max_snapshots (int): Maximum number of snapshots to take.

    Returns:
        int: Number of snapshots taken.
    """
    current_scroll = 0
    snapshot_count = 0
    last_height = total_height

    while current_scroll < total_height and snapshot_count < max_snapshots:
        driver.execute_script(f"window.scrollTo(0, {current_scroll});")
        time.sleep(scroll_pause_time)

        # Check for lazy-loaded content
        new_height = get_total_height(driver)
        if new_height > last_height:
            total_height = new_height
            logger.info(f"Page height increased to {total_height}px")
            last_height = new_height

        save_snapshot(driver, folder_name, snapshot_count)

        snapshot_count += 1
        current_scroll += viewport_height

    return snapshot_count

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

class DomainWorkerPool:
    def __init__(self, max_workers_per_domain=2):
        self.domain_pools = defaultdict(lambda: ThreadPoolExecutor(max_workers=max_workers_per_domain))
        self.max_workers_per_domain = max_workers_per_domain

    def submit(self, fn, url, *args, **kwargs):
        domain = urlparse(url).netloc
        return self.domain_pools[domain].submit(fn, url, *args, **kwargs)

    def shutdown(self):
        for pool in self.domain_pools.values():
            pool.shutdown()

def main() -> None:
    """
    Main function to run the web snapshot tool with improved error handling, execution time logging,
    and adaptive rate limiting.
    """
    start_time = time.time()

    parser = argparse.ArgumentParser(description='Capture snapshots of webpages.')
    parser.add_argument('input_file', type=str, help='Path to the input file containing URLs')
    parser.add_argument('--min_snapshots', type=int, default=DEFAULT_MIN_SNAPSHOTS, help='Minimum number of snapshots to capture')
    parser.add_argument('--max_snapshots', type=int, default=DEFAULT_MAX_SNAPSHOTS, help='Maximum number of snapshots to capture')
    parser.add_argument('--scroll_pause_time', type=float, default=SCROLL_PAUSE_TIME, help='Time to pause between scrolls')
    parser.add_argument('--max_workers_per_domain', type=int, default=2, help='Maximum number of workers per domain')
    parser.add_argument('--default_rate_limit', type=int, default=DEFAULT_RATE_LIMIT, help='Default rate limit per minute per domain')
    args = parser.parse_args()

    rate_limiter = AdaptiveRateLimiter(default_limit=args.default_rate_limit)

    urls = process_urls_from_file(args.input_file)
    
    domain_pool = DomainWorkerPool(max_workers_per_domain=args.max_workers_per_domain)
    
    try:
        future_to_url = {}
        for url in urls:
            if check_url_accessibility(url):
                future_to_url[domain_pool.submit(render_and_snapshot, url, BASE_OUTPUT_DIR, args.scroll_pause_time, args.min_snapshots, args.max_snapshots)] = url
            else:
                logger.warning(f"Skipping inaccessible URL: {url}")

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                logger.error(f'{url} generated an exception: {exc}')
    finally:
        domain_pool.shutdown()

    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()