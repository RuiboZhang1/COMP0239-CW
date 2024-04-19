from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import hashlib
import os
import redis
from celery import Celery
import requests
from io import BytesIO
from PIL import Image
from celery.utils.log import get_task_logger
import boto3
from botocore.exceptions import NoCredentialsError

# Initialize boto3 client
s3_client = boto3.client('s3')
BUCKET_NAME = 'comp0239-ucabrz5' 

logger = get_task_logger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/ec2-user/COMP0239-CW/uploaded_image/'

# Initialize Celery
celery = Celery(app.name)
celery.config_from_object('celeryconfig')

# Initialize Redis
r = redis.Redis(host='10.0.15.135', port=6379, db=0)

# processor = None
# model = None

def md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def file_md5(file_stream):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files and 'image_url' not in request.json:
        return jsonify(error="No file or image_url provided."), 400

    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify(error="No selected file."), 400
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_md5 = md5(file_path)

    elif 'image_url' in request.json:
        image_url = request.json['image_url']
        task = fetch_and_process_image.delay(image_url)
        return jsonify({"task_id": task.id}), 202

    if r.exists(image_md5):
        # Image already processed, fetch caption
        caption = r.get(image_md5).decode('utf-8')
        return jsonify(caption=caption)

    # Enqueue image processing task
    task = process_image.delay(file_path)
    return jsonify({"task_id": task.id}), 202

@celery.task(bind=True)
def fetch_and_process_image(self, image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        image_md5 = file_md5(image_bytes)
        # Reset file pointer after MD5 calculation
        image_bytes.seek(0)

        if r.exists(image_md5):
            caption = r.get(image_md5).decode('utf-8')
            return caption

        s3_key = f"{image_md5}.jpg"
        try:
            # Upload image to S3
            s3_client.upload_fileobj(image_bytes, BUCKET_NAME, s3_key)
        except NoCredentialsError:
            logger.error('AWS credentials not available')
            return None

        return process_image(s3_key)

    else:
        logger.error(f'Failed to fetch image from URL: {image_url}')
        raise ValueError(f"Error fetching image from {image_url}")

    
@celery.task(bind=True)
def process_image(self, s3_key):
    logger.info(f"Processing image with key: {s3_key}")
    try:
        # Download image from S3
        image_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        image = Image.open(image_obj['Body']).convert("RGB")
        image_md5 = s3_key.split('.')[0]

        if r.exists(image_md5):
                caption = r.get(image_md5).decode('utf-8')
        else:
            # Assuming 'processor' and 'model' are loaded in the worker initialization.
            global processor, model
            if processor is None or model is None:
                logger.error('Model or processor is not loaded.')
                raise ValueError('Model or processor is not loaded.')
        
            inputs = processor(images=image, return_tensors="pt")
            outputs = model.generate(**inputs)
            caption = processor.decode(outputs[0], skip_special_tokens=True)
            # Save the caption to Redis with MD5 as the key.
            r.set(image_md5, caption)
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
    except s3_client.exceptions.NoSuchKey:
        logger.error(f'Image key does not exist in S3: {s3_key}')
        return None

    return caption

if __name__ == '__main__':
    app.run(debug=True)
