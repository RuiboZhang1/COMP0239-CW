import requests
import os
import csv
import time
from datetime import datetime
from celery_task_app.utilities import extract_image_number

start_time = datetime.now()

# Constants
BATCH_SIZE = 1000  # Number of images to process per batch
END_LINE = 150000   # Total number of images to process
URL_FILE = "coco_image_urls.txt"

# URL of your Flask endpoint
endpoint = "http://18.133.220.62:4506/"

# Setup CSV file
csvfile = open('captions.csv', 'w', newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(['Image_Name', 'Task_ID', 'Caption'])

def poll_task_results(task_ids):
    """Polls the server for the results of the tasks."""
    results = {}
    while task_ids:
        for task_id in list(task_ids.keys()):
            result_endpoint = os.path.join(endpoint, "result", task_id)
            result_response = requests.get(result_endpoint)
            result_data = result_response.json()

            if result_data['state'] == 'SUCCESS':
                results[task_id] = result_data['result']
                task_ids.pop(task_id)
            elif result_data['state'] == 'FAILURE':
                results[task_id] = "Failed to get result"
                task_ids.pop(task_id)
            else:
                # Sleep before polling again to avoid overwhelming the server
                time.sleep(2)
    return results

# Process batches of images
start_line = 0
while start_line < END_LINE:
    # Read a batch of image URLs
    urls = []
    with open(URL_FILE, "r") as file:
        for i, line in enumerate(file):
            if i >= start_line and i < start_line + BATCH_SIZE:
                urls.append(line.strip())
            if i >= start_line + BATCH_SIZE:
                break

    # Upload images and collect task IDs
    task_ids = {}
    for url in urls:
        image_number = extract_image_number(url)
        upload_response = requests.post(os.path.join(endpoint, "upload"), json={"image_url": url})
        upload_data = upload_response.json()

        if 'caption' in upload_data:
            csvwriter.writerow([image_number, '', upload_data['caption']])
            csvfile.flush()
        elif 'task_id' in upload_data:
            task_ids[upload_data['task_id']] = image_number

    # Poll results for current batch
    captions = poll_task_results(task_ids.copy())
    for task_id, image_number in task_ids.items():
        caption = captions.get(task_id, "Can't Identify Image")
        csvwriter.writerow([image_number, task_id, caption])
        csvfile.flush()

    # Prepare for next batch
    start_line += BATCH_SIZE

# Close CSV file
csvfile.close()

# Compute and print the total running time
end_time = datetime.now()
duration = end_time - start_time
hours, remainder = divmod(duration.seconds, 3600)
minutes, seconds = divmod(remainder, 60)
print(f"All captions have been retrieved and written to the CSV file in {hours}h:{minutes}m:{seconds}s.")
