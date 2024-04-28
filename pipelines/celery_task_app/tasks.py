import logging
from celery import Task
from .ml.model import BlipModel
from .worker import celery
import requests
from io import BytesIO
from PIL import Image
from celery.utils.log import get_task_logger
from celery_task_app.utilities import file_md5
import boto3
from botocore.exceptions import NoCredentialsError
import redis

# Set up logging
logger = get_task_logger(__name__)

# Initialize boto3 S3 client, Redis, and Celery (Replace it with your bucket and redis address)
s3_client = boto3.client('s3')
BUCKET_NAME = 'comp0239-ucabrz5' 
r = redis.Redis(host='10.0.6.168', port=6379, db=0)


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


@celery.task(bind=True)
def fetch_and_process_image(self, image_url):
    """
    A task to fetch an image from a URL, calculate its MD5 hash, and then store the image in AWS S3.
    Subsequently, it calls another task to process the image.
    """
    logger.info(f"Fetching image from URL: {image_url}")
    response = requests.get(image_url)
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        image_md5 = file_md5(image_bytes)
        s3_key = f"{image_md5}.jpg"
        try:
            # Upload image to S3
            image_bytes.seek(0)  # Reset file pointer to the beginning before uploading
            s3_client.upload_fileobj(image_bytes, BUCKET_NAME, s3_key)
            return process_image(s3_key)
        except NoCredentialsError:
            logger.error('AWS credentials not available')
            return None
    else:
        logger.error(f'Failed to fetch image from URL: {image_url}')
        raise ValueError(f"Error fetching image from {image_url}")

    
@celery.task(ignore_result=False,
          bind=True,
          base=PredictTask,
          path=('celery_task_app.ml.model', 'BlipModel'),
          name='{}.{}'.format(__name__, 'Blip'))
def process_image(self, s3_key):
    """
    Process the image by loading it from S3, generating a caption using the ML model,
    and then storing the caption in Redis. It also handles cleaning up the S3 after processing.
    """
    logger.info(f"Processing image with key: {s3_key}")
    try:
        # Download image from S3
        image_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        try:
            image = Image.open(BytesIO(image_obj['Body'].read())).convert("RGB")
        except Exception as e:
            logger.error(f"Error processing image {s3_key}: {e}")
            return None

        image_md5 = s3_key.split('.')[0]

        if r.exists(image_md5): # Check if a caption is already stored
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
