# Install COCO API
"""
git clone https://github.com/cocodataset/cocoapi.git
cd cocoapi/PythonAPI
make
python setup.py install
"""

import requests
import zipfile
import io
from pycocotools.coco import COCO
import os
import random

# URL of the COCO dataset annotations zip file
url = "http://images.cocodataset.org/annotations/image_info_unlabeled2017.zip"

# Download the zip file from the URL
print("Downloading the annotations zip file...")
r = requests.get(url)
zip_content = r.content

# Unzip the content in memory
zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
zip_file.extractall('./')  # Extract it to the current working directory
print("Annotations zip file extracted.")

# Path to the COCO annotations file
annotations_path = './annotations/image_info_unlabeled2017.json'

# Initialize COCO API for instance annotations
coco = COCO(annotations_path)

# Retrieve all image ids
image_ids = coco.getImgIds()

# Randomly select 60000 image ids
selected_image_ids = random.sample(image_ids, 60000)

# Retrieve URLs for the selected images
image_urls = []
for img_id in selected_image_ids:
    img_info = coco.loadImgs(img_id)[0]
    image_urls.append(img_info['coco_url'])

# Do something with the image URLs, such as saving them to a file
with open('coco_image_urls.txt', 'w') as file:
    for url in image_urls:
        file.write(url + '\n')

print(f'Retrieved {len(image_urls)} image URLs from COCO dataset.')