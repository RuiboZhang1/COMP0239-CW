import requests
import os
import time

# Read the first 100 URLs from the text file
with open("coco_image_urls.txt", "r") as file:
    urls = [next(file).strip() for _ in range(100)]

# URL of your Flask endpoint
endpoint = "http://10.0.15.46:4200/"

def get_task_result(task_id):
    """Polls the server for the result of the task with the given task_id."""
    result_endpoint = os.path.join(endpoint, "result", task_id)
    while True:
        result_response = requests.get(result_endpoint)
        result_data = result_response.json()

        if result_data['state'] == 'PENDING':
            print("Task is still processing, waiting...")
            time.sleep(2)  # Wait for 2 seconds before polling again
        elif result_data['state'] == 'FAILURE':
            print(f"Task failed with error: {result_data.get('status')}")
            return None
        else:
            return result_data['result']

start = time.time()

# Send each URL to the Flask endpoint
for url in urls:
    upload_response = requests.post(os.path.join(endpoint, "upload"), json={"image_url": url})
    upload_data = upload_response.json()
    
    if 'task_id' in upload_data:
        print(f"Submitted URL {url}, waiting for result...")
        task_id = upload_data['task_id']
        caption = get_task_result(task_id)
        print(f"Caption for image {url}: {caption}")
    else:
        print(f"Failed to submit URL {url}, response: {upload_data}")

print(time.time() - start)