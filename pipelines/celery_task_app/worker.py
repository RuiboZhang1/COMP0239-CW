from celery import Celery

# Initialize Celery
celery = Celery('celery_app',
                broker='redis://10.0.15.135/0',
                backend='redis://10.0.15.135/1',
                include=['celery_task_app.tasks']
                )



