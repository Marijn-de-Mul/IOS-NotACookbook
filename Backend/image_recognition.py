import os
from google.cloud import vision
from google.cloud.vision_v1 import types
from PIL import Image

class ImageRecognizer:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def recognize(self, image_path):
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        response = self.client.label_detection(image=image)
        labels = response.label_annotations
        ingredients = [label.description for label in labels]
        return ingredients

    def load_image(self, image_file):
        image = Image.open(image_file).convert('RGB')
        return image