import requests
import zipfile
import io
from pycocotools.coco import COCO
import os
import random

def download_and_extract_annotations(url):
    print(f"Downloading the annotations zip file from {url}...")
    response = requests.get(url)
    zip_content = response.content

    # Unzip the content in memory
    zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
    zip_file.extractall('./')  # Extract it to the current working directory
    print(f"Annotations from {url} extracted.")

def get_image_urls(annotation_file):
    # Initialize COCO API for instance annotations
    coco = COCO(annotation_file)

    # Retrieve all image ids
    image_ids = coco.getImgIds()

    # Retrieve URLs for the selected images
    image_urls = []
    for img_id in image_ids:
        img_info = coco.loadImgs(img_id)[0]
        image_urls.append(img_info['coco_url'])
    return image_urls

# URLs of the COCO dataset annotations zip files
urls = [
    "http://images.cocodataset.org/annotations/image_info_unlabeled2017.zip",
    "http://images.cocodataset.org/annotations/image_info_test2017.zip"
]

# Process each dataset
all_image_urls = []
for url in urls:
    download_and_extract_annotations(url)
    if 'unlabeled' in url:
        annotations_path = './annotations/image_info_unlabeled2017.json'
    else:
        annotations_path = './annotations/image_info_test2017.json'
    image_urls = get_image_urls(annotations_path)
    all_image_urls.extend(image_urls)  # Combine URLs from both datasets

# Save all image URLs to a file
with open('coco_image_urls.txt', 'w') as file:
    for url in all_image_urls:
        file.write(url + '\n')

print(f'Retrieved a total of {len(all_image_urls)} image URLs from both COCO datasets.')
