import os
from ultralytics import YOLO

output_path = 'datasets/food41_yolo'

os.makedirs(output_path, exist_ok=True)
os.makedirs(os.path.join(output_path, 'images', 'train'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'images', 'val'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'labels', 'train'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'labels', 'val'), exist_ok=True)

class_names = [
    'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare', 'beet_salad', 'beignets', 'bibimbap',
    'bread_pudding', 'breakfast_burrito', 'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
    'ceviche', 'cheesecake', 'cheese_plate', 'chicken_curry', 'chicken_quesadilla', 'chicken_wings', 'chocolate_cake',
    'chocolate_mousse', 'churros', 'clam_chowder', 'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame',
    'cup_cakes', 'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots', 'falafel',
    'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari',
    'fried_rice', 'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon',
    'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream',
    'lasagna', 'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels',
    'nachos', 'omelette', 'onion_rings', 'oysters', 'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
    'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake',
    'risotto', 'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits', 'spaghetti_bolognese',
    'spaghetti_carbonara', 'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki', 'tiramisu',
    'tuna_tartare', 'waffles'
]

yaml_content = f"""
train: {os.path.abspath(os.path.join(output_path, 'images', 'train'))}
val: {os.path.abspath(os.path.join(output_path, 'images', 'val'))}

nc: {len(class_names)}  # number of classes
names: {class_names}  # list of class names
"""

yaml_file_path = os.path.join(output_path, 'food101.yaml')
with open(yaml_file_path, 'w') as f:
    f.write(yaml_content)

model = YOLO('../models/yolov5s.pt')  
model.train(data=yaml_file_path, epochs=50, batch=16, imgsz=640)

print("Model training completed.")