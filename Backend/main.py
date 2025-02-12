import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from image_recognition import ImageRecognizer
from recipe_generation import RecipeGenerator

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)
swagger = Swagger(app)

coco_class_names = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]
recognizer = ImageRecognizer('yolov5s.pt', coco_class_names)
generator = RecipeGenerator()

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': self.ingredients,
            'image_url': self.image_url
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
              image_url:
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
            image_url:
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            ingredients:
              type: string
            image_url:
              type: string
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
            image_url:
              type: string
    """
    data = request.get_json()
    recipe = Recipe(name=data['name'], ingredients=data['ingredients'], image_url=data.get('image_url'))
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            ingredients:
              type: string
            image_url:
              type: string
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
            image_url:
              type: string
    """
    data = request.get_json()
    recipe = Recipe.query.get_or_404(id)
    recipe.name = data['name']
    recipe.ingredients = data['ingredients']
    recipe.image_url = data.get('image_url')
    db.session.commit()
    return jsonify(recipe.as_dict())

@app.route('/recipes/<int:id>', methods=['DELETE'])
def delete_recipe(id):
    """
    Delete a recipe
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: No content
    """
    recipe = Recipe.query.get_or_404(id)
    db.session.delete(recipe)
    db.session.commit()
    return '', 204

@app.route('/process-image', methods=['POST'])
def process_image():
    """
    Process an image to extract ingredients and generate a recipe
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            image_url:
              type: string
    responses:
      200:
        description: The ingredients and generated recipe
        schema:
          type: object
          properties:
            ingredients:
              type: array
              items:
                type: string
            recipe:
              type: string
    """
    data = request.get_json()
    image_url = data['image_url']

    ingredients = recognizer.recognize(image_url)

    recipe = generator.generate_recipe(ingredients)

    return jsonify({
        'ingredients': ingredients,
        'recipe': recipe
    })

if __name__ == '__main__':
    app.run(debug=True)