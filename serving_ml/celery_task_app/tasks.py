import logging
from celery import Task
from .ml.model import BlipModel
from .worker import celery
import requests
from io import BytesIO
from PIL import Image
import hashlib
from celery.utils.log import get_task_logger
import boto3
from botocore.exceptions import NoCredentialsError
import redis


logger = get_task_logger(__name__)
s3_client = boto3.client('s3')
BUCKET_NAME = 'comp0239-ucabrz5' 
r = redis.Redis(host='10.0.15.135', port=6379, db=0)

def file_md5(file_stream):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

class PredictTask(Task):
    """
    Abstraction of Celery's Task class to support loading ML model.
    """
    abstract = True

    def __init__(self):
        super().__init__()
        self.model = None

    def __call__(self, *args, **kwargs):
        """
        Load model on first call (i.e. first task processed)
        Avoids the need to load model on each task request
        """
        if not self.model:
            logging.info('Loading Model...')
            self.model = BlipModel()
            logging.info("Model loaded")
        return self.run(*args, **kwargs)


# @celery.task(ignore_result=False,
#           bind=True,
#           base=PredictTask,
#           path=('celery_task_app.ml.model', 'BlipModel'),
#           name='{}.{}'.format(__name__, 'Blip'))
# def predict_caption(self, image):
#     """
#     Essentially the run method of PredictTask
#     """
#     pred_caption = self.model.predict(image)
#     return pred_caption


@celery.task(bind=True)
def fetch_and_process_image(self, image_url):
    logger.info(f"Fetching image from URL: {image_url}")
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

    
@celery.task(ignore_result=False,
          bind=True,
          base=PredictTask,
          path=('celery_task_app.ml.model', 'BlipModel'),
          name='{}.{}'.format(__name__, 'Blip'))
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
            caption = self.model.predict_caption(image)
            # Save the caption to Redis with MD5 as the key.
            r.set(image_md5, caption)
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
    except s3_client.exceptions.NoSuchKey:
        logger.error(f'Image key does not exist in S3: {s3_key}')
        return None
    
    return caption
