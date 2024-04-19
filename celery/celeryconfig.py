from celery.signals import worker_process_init
from celery import current_app


timezone = 'Europe/London'
broker_url = 'redis://10.0.15.135/0'  # Host's internal IP
result_backend = 'redis://10.0.15.135/1'  # Host's internal IP

task_soft_time_limit = 120  # Soft time limit in seconds
task_time_limit = 300  # Hard time limit in seconds

processor = None
model = None

@worker_process_init.connect
def load_model(**kwargs):
    from transformers import BlipProcessor, BlipForConditionalGeneration

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    
    current_app.conf.processor = processor
    current_app.conf.model = model