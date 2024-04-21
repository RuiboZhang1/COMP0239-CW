import requests
import os
import csv
import time
from celery_task_app.utilities import extract_image_number

start_line = 1  # Start reading from this line
end_line = 1000   # Read up to this line

# Read lines from start_line to end_line
urls = []
with open("coco_image_urls.txt", "r") as file:
    for current_line_number, line in enumerate(file, 1):
        if current_line_number >= start_line:
            urls.append(line.strip())
        if current_line_number == end_line:
            break


# URL of your Flask endpoint
endpoint = "http://10.0.15.46:4200/"

# CSV file creation
csvfile = open('captions.csv', 'w', newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(['Image_Name', 'Task_ID', 'Caption'])


def poll_task_results(task_ids):
    """Polls the server for the results of the tasks."""
    results = {}
    while task_ids:
        for task_id in list(task_ids.keys()):  # Use list to avoid dictionary size change during iteration
            # print(f"task_id: {task_id}")
            result_endpoint = os.path.join(endpoint, "result", task_id)
            result_response = requests.get(result_endpoint)
            result_data = result_response.json()

            # print(f"result data: {result_data}")

            if result_data['state'] == 'SUCCESS':
                results[task_id] = result_data['result']
                task_ids.pop(task_id)  # Remove completed task
            elif result_data['state'] == 'FAILURE':
                print(f"Task {task_id} failed with error: {result_data.get('status')}")
                results[task_id] = None
                task_ids.pop(task_id)  # Remove failed task
            # No need for an else block, let it loop until all tasks are done or failed
        time.sleep(2)  # Sleep before polling again
    return results

# Send each URL to the Flask endpoint
task_ids = {}
for url in urls:
    image_number = extract_image_number(url)
    upload_response = requests.post(os.path.join(endpoint, "upload"), json={"image_url": url})
    upload_data = upload_response.json()

    # The image is existed in the database, directly write the result to csv
    if 'caption' in upload_data:
        csvwriter.writerow([image_number, '', upload_data['caption']])
        csvfile.flush()
        print(f"Caption for existing image {url}: {upload_data['caption']}")

    # If image not existed, leave it for processing
    elif 'task_id' in upload_data:
        task_ids[upload_data['task_id']] = image_number  # Map task ID to image number
        print(f"Submitted URL {url}, task ID: {upload_data['task_id']}")

    
    # Wait 2 seconds to send a new image
    time.sleep(2)

# Poll all tasks and wait for their results
captions = poll_task_results(task_ids.copy())
# print(f"captions: {captions}")


# Write task results to CSV
for task_id, image_number in task_ids.items():
    caption = captions.get(task_id, "Can't Identify Image")  # Change here to get captions by task_id
    # print(f"caption: {caption}")
    csvwriter.writerow([image_number, task_id, caption])
    csvfile.flush()

# Close the CSV file when done
csvfile.close()

print("All captions have been retrieved and written to the CSV file.")