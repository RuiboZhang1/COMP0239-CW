import requests
import hashlib
from io import BytesIO

def md5(file_path):
    """
    Compute the MD5 hash of a file located at a specified path.
    This function reads the file in chunks to handle large files without using excessive memory.
    
    Args:
    file_path (str): The path to the file for which the MD5 hash is to be computed.

    Returns:
    str: The hexadecimal MD5 hash of the file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def file_md5_from_url(image_url):
    """
    Fetch an image from a URL and compute its MD5 hash using the file_md5 function.
    
    Args:
    image_url (str): The URL of the image.

    Returns:
    str: The MD5 hash of the image, or None if the image could not be fetched.
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        return file_md5(BytesIO(response.content))
    return None

def file_md5(file_stream):
    """
    Compute the MD5 hash of a file given as a file-like object (e.g., opened file or BytesIO).
    This function also processes the file in chunks to efficiently handle large files.
    
    Args:
    file_stream: A file-like object supporting read() method, from which to compute the hash.

    Returns:
    str: The hexadecimal MD5 hash of the contents of the file-like object.
    """
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to extract image number from URL
def extract_image_number(url):
    """
    Extract the image number from an image URL, assuming the URL ends with an image file name.
    
    Args:
    url (str): The URL of the image.

    Returns:
    str: The number extracted from the last segment of the URL, typically the image filename.
    """
    return url.split('/')[-1].split('.')[0]