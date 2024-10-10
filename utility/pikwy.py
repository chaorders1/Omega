#!/usr/bin/python3
import urllib.request
import urllib.parse
import os

def generate_screenshot_api_url(token, options):
  api_url = 'https://api.pikwy.com/?token=' + token
  if token:
    api_url += '&url=' + options.get('url', '')
    api_url += '&width=' + options.get('width', '1280')
    api_url += '&response_type=' + options.get('response_type', 'raw')
    api_url += '&full_page=' + options.get('full_page', '0')
    api_url += '&format=' + options.get('format', 'png')
    api_url += '&delay=' + options.get('delay', '10000')  # Wait 10 seconds
  return api_url

def read_urls_from_file(file_path: str) -> list:
    """
    Read URLs from a file.

    Args:
        file_path (str): The path to the file containing URLs.

    Returns:
        list: A list of URLs.
    """
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_screenshot(api_url: str, output_path: str) -> None:
    """
    Save a screenshot from the API URL to the specified output path.

    Args:
        api_url (str): The API URL to retrieve the screenshot.
        output_path (str): The path to save the screenshot.
    """
    urllib.request.urlretrieve(api_url, output_path)

def main():
    token = '4ee4b1c1b677dda6f3098b95fd2bc1dc51d6a46cd1831201'
    options = {
        'width': '1280',
        'response_type': 'raw',
        'full_page': '1',
        'format': 'png',
        'delay': '10000'
    }

    # Use the same data folder as in crawl_script.py
    data_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data')
    urls_file_path = os.path.join(data_folder, 'blank.txt')

    urls = read_urls_from_file(urls_file_path)
    output_dir = os.path.join(data_folder, 'web_snapshots')
    os.makedirs(output_dir, exist_ok=True)

    for url in urls:
        options['url'] = url
        api_url = generate_screenshot_api_url(token, options)
        output_path = os.path.join(output_dir, f"{urllib.parse.quote(url, safe='')}.png")
        save_screenshot(api_url, output_path)
        print(f"Saved screenshot for {url} to {output_path}")

if __name__ == "__main__":
    main()