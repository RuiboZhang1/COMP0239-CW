from captionGenerateTasks import save_image, generate_caption
from celery import chain
import time

img_urls = ['http://images.cocodataset.org/unlabeled2017/000000562987.jpg',
            'http://images.cocodataset.org/unlabeled2017/000000369693.jpg',
            'http://images.cocodataset.org/unlabeled2017/000000385948.jpg']
results = []

# Chain function to process the image
def process_image_chain(img_urls):
    for img_url in img_urls:
        results.append(chain(save_image.s(img_url), generate_caption.s())())
    # result = save_image.delay(img_url)
    # while True: 
    #     if result.ready:
    #         img_path = result.get()
    #         break

    # # result = load_model.delay()
    # # while True: 
    # #     if result.ready:
    # #         processor, model = result.get()
    # #         break
    
    # result = generate_caption.delay(img_path)
    # while True: 
    #     if result.ready:
    #         caption = result.get()
    #         break
    # return caption

start = time.time()
process_image_chain(img_urls)

for result in results:
    print(result.get())

print(f"time used: ", {time.time() - start})