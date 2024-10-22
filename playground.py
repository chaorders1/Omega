import requests
from tqdm import tqdm
import os

def download_file(url, output_path=None):
    """
    Download a file from the given URL and save it to the specified output path.

    Args:
        url (str): The URL of the file to download.
        output_path (str, optional): The path where the file should be saved.
            If not provided, the file will be saved in the current directory
            with the name 'downloaded_video.mp4'.

    Returns:
        str: The path where the file was saved.
    """
    try:
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Get the file size from the headers
        total_size = int(response.headers.get('content-length', 0))

        # If output_path is not provided, use a default name
        if output_path is None:
            output_path = 'downloaded_video.mp4'

        # Open the output file and write the content
        with open(output_path, 'wb') as file, tqdm(
            desc=output_path,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)

        print(f"File downloaded successfully: {output_path}")
        return output_path

    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

if __name__ == "__main__":
    # The URL of the file to download
    url = "https://rr1---sn-oxunxg8pjvn-bg0rl.googlevideo.com/videoplayback?expire=1729143302&ei=pk0QZ8XzMLaPobIPrLiz4Q4&ip=2804%3A14c%3A179%3A966e%3A1f7%3Aa959%3Ab6f8%3A1c6&id=o-ANpBkQQDycsQtRrAImrqjuIGbmHkpCeXERE4gG7vnPED&itag=18&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&met=1729121702%2C&mh=T_&mm=31%2C29&mn=sn-oxunxg8pjvn-bg0rl%2Csn-bg0s7n7e&ms=au%2Crdu&mv=m&mvi=1&pl=44&rms=au%2Cau&initcwndbps=891250&bui=AXLXGFRZ-0KGUaqeRT0hnQCt68_UXp01YL1slsC4pKwYZlUiqw9ZiaWehqcUTchHf_MgsDRppc0Ba45W&spc=54MbxeTI4nBAxJsVSwNpVEoetKYeWsWwRf0kWO-Zq24fxwra-oEZT36rjXGrgx3lEQ&vprv=1&svpuc=1&mime=video%2Fmp4&ns=b3CP1ln3WZnlI-Qu-1vkPMIQ&rqh=1&gir=yes&clen=73823580&ratebypass=yes&dur=3756.547&lmt=1727815698386633&mt=1729121361&fvip=4&fexp=51286684%2C51300761%2C51312688&c=WEB&sefc=1&txp=5438434&n=zvuX_h5Dy7iEmQ&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cbui%2Cspc%2Cvprv%2Csvpuc%2Cmime%2Cns%2Crqh%2Cgir%2Cclen%2Cratebypass%2Cdur%2Clmt&sig=AJfQdSswRAIgYROf-HYFVUA3OSAVy72QH_1QoTluwpMJmOT0CoH0IGsCIGc3_SY-K0_0mfZl_k4YnndNRJBRLLSeDoosjurDQGW9&lsparams=met%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Crms%2Cinitcwndbps&lsig=ACJ0pHgwRAIgeErotzVS4uRWwW_BywmgQUWZ_E6RBY0x0irWAwTyjR4CIB7dL-A3FCfN9GX-qUyBGSHSpmK7tIMmnqODsDQYXEAv"

    # Download the file
    downloaded_file = download_file(url)
    if downloaded_file:
        print(f"File saved to: {downloaded_file}")
    else:
        print("Download failed.")
