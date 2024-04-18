from celery import Celery
app = Celery('celery_app')
app.config_from_object('celeryconfig')

@app.task
def multiply(x, y):
    return x * y
