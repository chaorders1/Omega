#!/usr/bin/python3
import urllib.request
import urllib.parse

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

token = '4ee4b1c1b677dda6f3098b95fd2bc1dc51d6a46cd1831201'
options = {
  'url': 'https://www.youtube.com/@wangzhian/videos',
  'width': '1280',
  'response_type': 'raw',
  'full_page': '1',  # Capture full page
  'format': 'png',   # PNG format
  'delay': '10000'   # Wait 10 seconds
}

api_url = generate_screenshot_api_url(token, options)

opener = urllib.request.build_opener()
urllib.request.install_opener(opener)
output = 'output.png'
urllib.request.urlretrieve(api_url, output)