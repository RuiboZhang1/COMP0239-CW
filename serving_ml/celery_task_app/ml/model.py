from transformers import BlipProcessor, BlipForConditionalGeneration

class BlipModel:
    """ Wrapper for loading and serving pre-trained model"""
    def __init__(self):
        self.processor, self.model = self._load_models()
        

    @staticmethod
    def _load_models():
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

        return processor, model

    def predict_caption(self, image):
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        caption = self.processor.decode(outputs[0], skip_special_tokens=True)
        return caption