import os
import h5py
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

dataset_path = 'datasets/food41'
output_path = 'datasets/food41_yolo'
os.makedirs(output_path, exist_ok=True)
os.makedirs(os.path.join(output_path, 'images', 'train'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'images', 'val'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'labels', 'train'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'labels', 'val'), exist_ok=True)

with h5py.File(os.path.join(dataset_path, 'food_c101_n1000_r384x384x3.h5'), 'r') as f:
    images = f['images'][:]
    labels = f['category'][:]

train_images, val_images, train_labels, val_labels = train_test_split(images, labels, test_size=0.2, random_state=42)

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

def save_yolo_format(images, labels, subset):
    for i, (image, label) in enumerate(zip(images, labels)):
        image = Image.fromarray(image)
        image_path = os.path.join(output_path, 'images', subset, f'{i}.jpg')
        label_path = os.path.join(output_path, 'labels', subset, f'{i}.txt')
        
        image.save(image_path)
        
        with open(label_path, 'w') as f:
            class_id = label
            center_x = 0.5
            center_y = 0.5
            width = 1.0
            height = 1.0
            f.write(f'{class_id} {center_x} {center_y} {width} {height}\n')

save_yolo_format(train_images, train_labels, 'train')
save_yolo_format(val_images, val_labels, 'val')

print("Dataset converted to YOLO format.")