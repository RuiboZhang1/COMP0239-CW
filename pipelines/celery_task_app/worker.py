from celery import Celery

# Initialize Celery
celery = Celery('celery_app',
                broker='redis://10.0.6.168/0',
                backend='redis://10.0.6.168/1',
                include=['celery_task_app.tasks']
                )



