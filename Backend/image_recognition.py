import torch
from PIL import Image

class ImageRecognizer:
    def __init__(self, model_path, class_names):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)
        self.class_names = class_names

    def recognize(self, image_path):
        image = Image.open(image_path)
        results = self.model(image)
        labels = results.xyxyn[0][:, -1].numpy()
        ingredients = [self.class_names[int(label)] for label in labels if int(label) < len(self.class_names)]
        return ingredients