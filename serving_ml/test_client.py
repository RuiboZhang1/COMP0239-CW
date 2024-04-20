import requests
import os
import csv
import time
from celery_task_app.utilities import extract_image_number

start_line = 1  # Start reading from this line
end_line = 30   # Read up to this line

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
        
def poll_task_results(task_ids):
    """Polls the server for the results of the tasks."""
    results = {}
    while task_ids:
        for task_id in list(task_ids.keys()):  # Use list to avoid dictionary size change during iteration
            result_endpoint = os.path.join(endpoint, "result", task_id)
            result_response = requests.get(result_endpoint)
            result_data = result_response.json()

            if result_data['state'] == 'SUCCESS':
                results[task_ids[task_id]] = result_data['result']
                task_ids.pop(task_id)  # Remove completed task
            elif result_data['state'] == 'FAILURE':
                print(f"Task {task_id} failed with error: {result_data.get('status')}")
                results[task_ids[task_id]] = None
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
    
    if 'task_id' in upload_data:
        print(f"Submitted URL {url}, task ID: {upload_data['task_id']}")
        task_ids[upload_data['task_id']] = image_number  # Map task ID to image number
    
    time.sleep(2)

# Poll all tasks and wait for their results
captions = poll_task_results(task_ids)

# Write results to CSV
with open('captions.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Image_Name', 'Task_ID', 'Caption'])

    for task_id, image_number in task_ids.items():
        caption = captions.get(image_number, "Can't Identity Image")
        csvwriter.writerow([image_number, task_id, caption])
        csvfile.flush()  # Flush after each row

print("All captions have been retrieved and written to the CSV file.")

# # CSV file creation
# with open('captions.csv', 'w', newline='') as csvfile:
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(['Image_Name', 'Task_ID', 'Caption'])

#     start = time.time()

#     # Send each URL to the Flask endpoint and write to CSV
#     for url in urls:
#         image_number = extract_image_number(url)
#         upload_response = requests.post(os.path.join(endpoint, "upload"), json={"image_url": url})
#         upload_data = upload_response.json()
        
#         if 'task_id' in upload_data:
#             print(f"Submitted URL {url}, waiting for result...")
#             task_id = upload_data['task_id']
#             caption = get_task_result(task_id)
#             csvwriter.writerow([image_number, task_id, caption if caption else "Can't Identity Image"])
#             csvfile.flush()
#             if caption:
#                 print(f"Caption for image {url}: {caption}")
#             else:
#                 print(f"Failed to get caption for image {url}")
#         else:
#             caption = upload_data.get('caption', '')
#             csvwriter.writerow([image_number, '', caption])
#             csvfile.flush()
#             print(f"Image {image_number} is existed, caption: {caption}")
        
#         time.sleep(2)

#     print(time.time() - start)