import logging
import boto3
import redis
import os
import time

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from celery import Celery, Task
from celery.utils.log import get_task_logger
from celery_task_app.tasks import fetch_and_process_image, process_image
from celery_task_app.utilities import md5, file_md5_from_url, file_md5
from io import BytesIO
from PIL import Image
from botocore.exceptions import NoCredentialsError, ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

# Initialize Flask app and Celery
app = Flask(__name__)
celery = Celery(app.name, broker='redis://10.0.6.168/0', backend='redis://10.0.6.168/1')

# Initialize Redis and S3 client
r = redis.Redis(host='10.0.6.168', port=6379, db=0)
s3_client = boto3.client('s3')
BUCKET_NAME = 'comp0239-ucabrz5'

def save_image_to_s3(file_stream, s3_key, max_retries=3, backoff_factor=2):
    """Upload image file stream to S3 with retries and exponential backoff."""
    for attempt in range(max_retries):
        try:
            file_stream.seek(0)  # Reset file pointer to the beginning
            s3_client.upload_fileobj(file_stream, BUCKET_NAME, s3_key)
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.error(f'Attempt {attempt + 1} failed with error: {e}')
            time.sleep(backoff_factor ** attempt)
    return False

def get_caption_or_task(image_md5, s3_key=None, image_url=None, max_retries=3):
    """Check if image has been processed, or start a processing task with retries."""
    for attempt in range(max_retries):
        try:
            if r.exists(image_md5):
                return 'caption', r.get(image_md5).decode('utf-8')
            elif s3_key:
                task = process_image.delay(s3_key)
                return 'task_id', task.id
            elif image_url:
                task = fetch_and_process_image.delay(image_url)
                return 'task_id', task.id
            else:
                return 'error', 'No image data provided'
        except redis.exceptions.ConnectionError as e:
            logger.error(f'Redis connection error on attempt {attempt + 1}: {e}')
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')
            return 'error', str(e)


# Define route handlers
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint to handle file uploads and image processing."""
     # Handle file upload from form data
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify(error="No selected file."), 400
        file_stream = file.stream
        image_md5 = file_md5(file_stream)
        s3_key = f"{image_md5}.jpg"
        if save_image_to_s3(file_stream, s3_key):
            result_type, result_data = get_caption_or_task(image_md5, s3_key=s3_key)
        else:
            return jsonify(error="Failed to upload to S3."), 500
    # Handle image URL in JSON payload
    elif 'image_url' in request.json:
        image_url = request.json['image_url']
        image_md5 = file_md5_from_url(image_url)
        result_type, result_data = get_caption_or_task(image_md5, image_url=image_url)
        if result_type == 'error':
            # If after retries an error still occurs, return an error response
            return jsonify(error=result_data), 500
    else:
        return jsonify(error="No file or image_url provided."), 400
    
    return jsonify({result_type: result_data}), 202 if result_type == 'task_id' else 200


@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    result = celery.AsyncResult(task_id)

    if result.state == 'PENDING':
        return jsonify({'state': result.state, 'status': 'Task is still processing'}), 202
    elif result.state == 'FAILURE':
        return jsonify({'state': result.state, 'status': str(result.info)}), 500
    return jsonify({'state': result.state, 'result': result.result}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4506)