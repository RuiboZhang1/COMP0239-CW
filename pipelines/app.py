from celery.result import AsyncResult
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import redis
from celery.utils.log import get_task_logger
import boto3
from celery_task_app.tasks import fetch_and_process_image, process_image
from celery_task_app.utilities import md5, file_md5_from_url
from celery import Celery

# Initialize boto3 client
s3_client = boto3.client('s3')
BUCKET_NAME = 'comp0239-ucabrz5' 

logger = get_task_logger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/ec2-user/COMP0239-CW/uploaded_image/'
celery = Celery(app.name, broker='redis://10.0.15.135/0', backend='redis://10.0.15.135/1')

# Initialize Redis
r = redis.Redis(host='10.0.15.135', port=6379, db=0)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Create celery prediction task. Return task_id or result directly to the client."""

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
        image_md5 = file_md5_from_url(image_url)  # Assume this function exists

    # Check if the image has already been processed
    if r.exists(image_md5):
        # Image already processed, fetch caption
        caption = r.get(image_md5).decode('utf-8')
        return jsonify({"caption": caption})

    # Enqueue image processing task
    if 'file' in request.files:
        task = process_image.delay(file_path)
    else:
        task = fetch_and_process_image.delay(image_url)
    return jsonify({"task_id": task.id}), 202


@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    result = celery.AsyncResult(task_id)
    if result.state == 'PENDING':
        return jsonify({'state': result.state, 'status': 'Task is still processing'}), 202
    elif result.state == 'FAILURE':
        return jsonify({'state': result.state, 'status': str(result.info)}), 500
    return jsonify({'state': result.state, 'result': result.result}), 200