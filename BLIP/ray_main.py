import os
import uuid
import requests
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import hashlib
import json
import ray

# Initialize Ray
ray.init(address='auto')  # Connects to the cluster

# Download image and process in memory
def download_image(img_url):
    response = requests.get(img_url, stream=True)
    response.raise_for_status()
    img_bytes = response.content
    image = Image.open(BytesIO(img_bytes)).convert('RGB')
    return image

# Load model
@ray.remote
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

# Generate and store caption
@ray.remote
def generate_caption(image, processor, model, device):
    inputs = processor(images=image, return_tensors="pt").to(device)
    outputs = model.generate(**inputs)
    caption = processor.decode(outputs[0], skip_special_tokens=True)
    return caption

@ray.remote
def process_image(img_url, processor, model, device):
    image = download_image(img_url)
    
    # Compute MD5 hash of the image for a unique key
    img_hash = hashlib.md5(image.tobytes()).hexdigest()
    
    caption = generate_caption.remote(image, processor, model, device)
    caption_val = ray.get(caption)
    
    # Save key-value pair to Redis (MD5 hash -> caption)
    redis_client.set(img_hash, caption_val)
    return img_hash

def distribute_caption_generation(img_urls):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Assume Redis and Ray are on the same network or properly configured for access
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

    future_model = load_model.remote()
    processor, model = ray.get(future_model)

    [process_image.remote(img_url, processor, model, device) for img_url in img_urls]


if __name__ == "__main__":
    img_urls = ["list", "of", "image", "URLs"]  # Load or pass your list of image URLs here
    captions = distribute_caption_generation(img_urls)
    print(captions)
