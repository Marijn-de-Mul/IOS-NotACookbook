import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from werkzeug.utils import secure_filename
from image_recognition import ImageRecognizer
from recipe_generation import RecipeGenerator

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
db = SQLAlchemy(app)
swagger = Swagger(app)

food101_class_names = [
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
recognizer = ImageRecognizer('models/yolov5s.pt', food101_class_names)
generator = RecipeGenerator()

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200), nullable=True) 

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': self.ingredients,
            'image_path': self.image_path
        }

with app.app_context():
    db.create_all()

@app.route('/recipes', methods=['GET'])
def get_recipes():
    """
    Get all recipes
    ---
    responses:
      200:
        description: A list of recipes
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              ingredients:
                type: string
              image_path:
                type: string
    """
    recipes = Recipe.query.all()
    return jsonify([recipe.as_dict() for recipe in recipes])

@app.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id):
    """
    Get a single recipe by ID
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: A single recipe
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            ingredients:
              type: string
            image_path:
              type: string
    """
    recipe = Recipe.query.get_or_404(id)
    return jsonify(recipe.as_dict())

@app.route('/recipes', methods=['POST'])
def add_recipe():
    """
    Add a new recipe
    ---
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: ingredients
        in: formData
        type: string
        required: true
      - name: image
        in: formData
        type: file
        required: false
    responses:
      201:
        description: The created recipe
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            ingredients:
              type: string
            image_path:
              type: string
    """
    name = request.form['name']
    ingredients = request.form['ingredients']
    image = request.files.get('image')

    image_path = None
    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

    recipe = Recipe(name=name, ingredients=ingredients, image_path=image_path)
    db.session.add(recipe)
    db.session.commit()
    return jsonify(recipe.as_dict()), 201

@app.route('/recipes/<int:id>', methods=['PUT'])
def update_recipe(id):
    """
    Update an existing recipe
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: name
        in: formData
        type: string
        required: true
      - name: ingredients
        in: formData
        type: string
        required: true
      - name: image
        in: formData
        type: file
        required: false
    responses:
      200:
        description: The updated recipe
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            ingredients:
              type: string
            image_path:
              type: string
    """
    recipe = Recipe.query.get_or_404(id)
    name = request.form['name']
    ingredients = request.form['ingredients']
    image = request.files.get('image')

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        recipe.image_path = image_path

    recipe.name = name
    recipe.ingredients = ingredients
    db.session.commit()
    return jsonify(recipe.as_dict())

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image using the AI model
    ---
    parameters:
      - name: image
        in: formData
        type: file
        required: true
    responses:
      200:
        description: The analysis result
        schema:
          type: object
          properties:
            class_name:
              type: string
            confidence:
              type: number
    """
    image = request.files.get('image')
    if not image:
        return jsonify({'error': 'No image uploaded'}), 400

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    ingredients = recognizer.recognize(image_path)

    recipe_name, recipe_text = generator.generate_recipe(ingredients)

    recipe = Recipe(name=recipe_name, ingredients=recipe_text, image_path=image_path)
    db.session.add(recipe)
    db.session.commit()

    return jsonify(recipe.as_dict())
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)