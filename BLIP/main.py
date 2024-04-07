import os

# Set up custom paths
custom_hf_dir = '/home/ec2-user/data/cache'  # Directory to store Hugging Face cache and models
os.environ['HF_HOME'] = custom_hf_dir  # Set environment variable for Hugging Face

import os
import uuid
import requests
import boto3
from PIL import Image
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
from transformers import BlipProcessor, BlipForConditionalGeneration
import json
from prefect import flow, task
from prefect.task_runners import RayTaskRunner
import ray

# Initialize Ray
ray.init(address='auto')

# Global Variable
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
s3_client = boto3.client('s3')
bucket_name = 'comp0239-ucabrz5'

# This function receives a img url, download the img and store it to S3 bucket
@task
def get_and_save_image(img_url):
    response = requests.get(img_url, stream=True)
    response.raise_for_status()
    img_path = f"/tmp/{uuid.uuid4()}.jpg"  # Temporary save path
    with open(img_path, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)
    
    # Generate a unique directory name for this image
    unique_folder = str(uuid.uuid4())
    s3_path = f"images/{unique_folder}/image.jpg"
    
    s3_client.upload_file(img_path, bucket_name, s3_path)

    image = Image.open(img_path).convert('RGB')

    # Cleanup the local file
    os.remove(img_path)

    return image, s3_path  

# This function is loading the pretrained model
@task
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

@task
def generate_caption(image, processor, model):    
    inputs = processor(images=image, return_tensors="pt").to(device)
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption


# This function save the generated captions to the S3 bucket.
@task
def save_caption(caption, s3_path):
    # Change the path to store the caption as a .json file
    caption_path = s3_path.replace('image.jpg', 'caption.json')
    caption_data = {"caption": caption}
    
    # Create a JSON string from the caption
    caption_json = json.dumps(caption_data)
    
    # Save the caption to S3
    s3_client.put_object(Body=caption_json, Bucket=bucket_name, Key=caption_path)

@flow
def process_image_url(img_url):
    image, s3_path = get_and_save_image(img_url)
    processor, model = load_model()
    caption = generate_caption(image, processor, model)
    print(caption)
    save_caption(caption, s3_path)

@flow(task_runner=RayTaskRunner())
def distribute_caption_generation(img_urls_file):
    # Read the image URLs from the file
    with open(img_urls_file, 'r') as f:
        img_urls = f.read().splitlines()
    
    # Distribute the image processing tasks across the Ray cluster
    for img_url in img_urls:
        process_image_url(img_url)

if __name__ == "__main__":
    distribute_caption_generation("/home/ec2-user/COMP0239-CW/BLIP/coco_image_urls.txt")
