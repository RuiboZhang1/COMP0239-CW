import requests
import hashlib
from io import BytesIO

def md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def file_md5_from_url(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return file_md5(BytesIO(response.content))
    return None

def file_md5(file_stream):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to extract image number from URL
def extract_image_number(url):
    return url.split('/')[-1].split('.')[0]