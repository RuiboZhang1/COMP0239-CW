from celery import Celery

app = Celery('tasks')
app.config_from_object('celeryconfig')


@app.task
def add(x, y):
    return x + y

@app.task
def divide(x, y):
    return x / y

@app.task
def multiply(x, y):
    return x*y

@app.task
def subtract(x, y):
    return x-y

@app.task
def power(x, y): 
    val = x[0]
    return val ** y

@app.task
def mean(x):
    return [sum(x)/len(x)]

@app.task
def diff_vect(x, y):
    diffs = []
    mean = x[0]
    for value in y:
        print(value)
        diffs.append(value - mean)
    return diffs

@app.task
def sq_vect(x):
    sqs = []
    for value in x:
        sqs.append(value ** 2)
    return sqs

    