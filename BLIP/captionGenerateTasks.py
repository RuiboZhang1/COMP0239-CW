import os
import uuid
import requests
from PIL import Image
from celery import Celery
from transformers import BlipProcessor, BlipForConditionalGeneration

# Configure Celery
app = Celery('tasks')
app.config_from_object('celeryconfig')

# Task to download and save image
@app.task
def save_image(img_url):
    response = requests.get(img_url, stream=True)
    response.raise_for_status()
    img_path = f"/tmp/{uuid.uuid4()}.jpg"
    with open(img_path, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)
    return img_path

# Task to load the model
# @app.task
# def load_model():
#     processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
#     model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
#     return processor, model

# Task to generate and save caption
@app.task
def generate_caption(img_path):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    image = Image.open(img_path).convert('RGB')
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    os.remove(img_path)  # Clean up the temporary image file
    return caption