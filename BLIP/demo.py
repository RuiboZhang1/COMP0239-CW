import os

# Set up custom paths
custom_hf_dir = '/home/ec2-user/data/cache'  # Directory to store Hugging Face cache and models
os.environ['HF_HOME'] = custom_hf_dir  # Set environment variable for Hugging Face

# # Set up custom paths
# custom_model_dir = '/home/ec2-user/data/models'  # Directory to store models
# custom_image_dir = '/home/ec2-user/data/images'  # Directory to store images
# os.environ['HF_HOME'] = custom_model_dir  # Set environment variable for transformers

import sys
from PIL import Image
import requests
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
from transformers import BlipProcessor, BlipForConditionalGeneration
from models.blip import blip_decoder
import time
import logging

logging.basicConfig(level=logging.INFO)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def save_image(img_url, img_path):
    response = requests.get(img_url, stream=True)
    response.raise_for_status()  # Ensure the request was successful
    with open(img_path, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)
    return Image.open(img_path).convert('RGB')

def load_demo_image(image_size, device, image_path):
    # img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg' 
    # raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')   
    raw_image = Image.open(image_path).convert('RGB') 

    w,h = raw_image.size
    # display(raw_image.resize((w//5,h//5)))
    
    transform = transforms.Compose([
        transforms.Resize((image_size,image_size),interpolation=InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ]) 
    image = transform(raw_image).unsqueeze(0).to(device)   
    return image

start = time.time()

# # Make sure the directories exist
# os.makedirs(custom_model_dir, exist_ok=True)
# os.makedirs(custom_image_dir, exist_ok=True)

# Make sure the Hugging Face cache directory exists
os.makedirs(os.path.join(custom_hf_dir, 'images'), exist_ok=True)


# Define paths
demo_image_path = os.path.join(custom_hf_dir, 'images', 'demo.jpg')
img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg'
save_image(img_url, demo_image_path)

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

raw_image = save_image(img_url, demo_image_path)
inputs = processor(raw_image, return_tensors="pt")
out = model.generate(**inputs)
print(processor.decode(out[0], skip_special_tokens=True))

print(time.time() - start)

# image_size = 384
# image = load_demo_image(image_size=image_size, device=device)

# model_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_capfilt_large.pth'
    
# model = blip_decoder(pretrained=model_url, image_size=image_size, vit='base')
# model.eval()
# model = model.to(device)

# with torch.no_grad():
#     # beam search
#     caption = model.generate(image, sample=False, num_beams=3, max_length=20, min_length=5) 
#     # nucleus sampling
#     # caption = model.generate(image, sample=True, top_p=0.9, max_length=20, min_length=5) 
#     print('caption: '+caption[0])