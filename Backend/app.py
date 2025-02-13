import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from werkzeug.utils import secure_filename
from image_recognition import ImageRecognizer
from recipe_generation import RecipeGenerator
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
app.config['JWT_SECRET_KEY'] = '0cf963cb58107b1b7ab52d2642ca8a4fc40bfe072a03bfaec0536a17c876f77d89f53261d96b8a57d9b9530bcbf4157e1b1d7d20f3f7fee3c86119a9911502dd' 
db = SQLAlchemy(app)
swagger = Swagger(app)
jwt = JWTManager(app)

recognizer = ImageRecognizer()
generator = RecipeGenerator(api_key=os.getenv('OPENAI_API_KEY'))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('recipes', lazy=True))

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': self.ingredients,
            'image_path': self.image_path,
            'user_id': self.user_id
        }

with app.app_context():
    db.create_all()

@app.before_request
def log_request_info():
    logger.info(f"Request Headers: {request.headers}")
    logger.info(f"Request Body: {request.get_data()}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response Status: {response.status}")
    logger.info(f"Response Headers: {response.headers}")
    logger.info(f"Response Body: {response.get_data()}")
    return response

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - User
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: The username for the new user
            password:
              type: string
              description: The password for the new user
    responses:
      201:
        description: User registered successfully
      400:
        description: Username and password are required or Username already exists
    """
    logger.info("Register endpoint called")
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        logger.warning("Username and password are required")
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        logger.warning("Username already exists")
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info("User registered successfully")
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Login a user
    ---
    tags:
      - User
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: The username of the user
            password:
              type: string
              description: The password of the user
    responses:
      200:
        description: User logged in successfully
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: The JWT access token
      400:
        description: Username and password are required
      401:
        description: Invalid username or password
    """
    logger.info("Login endpoint called")
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        logger.warning("Username and password are required")
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        logger.warning("Invalid username or password")
        return jsonify({'error': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=str(user.id))  
    logger.info("User logged in successfully")
    return jsonify({'access_token': access_token}), 200

@app.route('/recipes', methods=['GET'])
@jwt_required()
def get_recipes():
    """
    Get all recipes for the authenticated user
    ---
    tags:
      - Recipe
    responses:
      200:
        description: A list of recipes
        schema:
          type: array
          items:
            $ref: '#/definitions/Recipe'
    """
    logger.info("Get recipes endpoint called")
    user_id = get_jwt_identity()
    recipes = Recipe.query.filter_by(user_id=user_id).all()
    logger.info(f"Fetched {len(recipes)} recipes for user {user_id}")
    return jsonify([recipe.as_dict() for recipe in recipes])

@app.route('/recipes/<int:id>', methods=['GET'])
@jwt_required()
def get_recipe(id):
    """
    Get a specific recipe by ID for the authenticated user
    ---
    tags:
      - Recipe
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the recipe
    responses:
      200:
        description: The recipe details
        schema:
          $ref: '#/definitions/Recipe'
      404:
        description: Recipe not found
    """
    logger.info(f"Get recipe endpoint called for recipe ID {id}")
    user_id = get_jwt_identity()
    recipe = Recipe.query.filter_by(id=id, user_id=user_id).first_or_404()
    logger.info(f"Fetched recipe {id} for user {user_id}")
    return jsonify(recipe.as_dict())

@app.route('/recipes', methods=['POST'])
@jwt_required()
def add_recipe():
    """
    Add a new recipe for the authenticated user
    ---
    tags:
      - Recipe
    parameters:
      - name: name
        in: formData
        type: string
        required: true
        description: The name of the recipe
      - name: ingredients
        in: formData
        type: string
        required: true
        description: The ingredients of the recipe
      - name: image
        in: formData
        type: file
        required: false
        description: An optional image of the recipe
    responses:
      201:
        description: Recipe added successfully
        schema:
          $ref: '#/definitions/Recipe'
    """
    logger.info("Add recipe endpoint called")
    user_id = get_jwt_identity()
    name = request.form['name']
    ingredients = request.form['ingredients']
    image = request.files.get('image')

    image_path = None
    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

    recipe = Recipe(name=name, ingredients=ingredients, image_path=image_path, user_id=user_id)
    db.session.add(recipe)
    db.session.commit()
    logger.info(f"Added recipe {recipe.id} for user {user_id}")
    return jsonify(recipe.as_dict()), 201

@app.route('/recipes/<int:id>', methods=['PUT'])
@jwt_required()
def update_recipe(id):
    """
    Update a recipe by ID for the authenticated user
    ---
    tags:
      - Recipe
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the recipe
      - name: name
        in: formData
        type: string
        required: true
        description: The name of the recipe
      - name: ingredients
        in: formData
        type: string
        required: true
        description: The ingredients of the recipe
      - name: image
        in: formData
        type: file
        required: false
        description: An optional image of the recipe
    responses:
      200:
        description: Recipe updated successfully
        schema:
          $ref: '#/definitions/Recipe'
      404:
        description: Recipe not found
    """
    logger.info(f"Update recipe endpoint called for recipe ID {id}")
    user_id = get_jwt_identity()
    recipe = Recipe.query.filter_by(id=id, user_id=user_id).first_or_404()
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
    logger.info(f"Updated recipe {id} for user {user_id}")
    return jsonify(recipe.as_dict())

@app.route('/recipes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(id):
    """
    Delete a recipe by ID for the authenticated user
    ---
    tags:
      - Recipe
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the recipe
    responses:
      200:
        description: Recipe deleted successfully
      404:
        description: Recipe not found
    """
    logger.info(f"Delete recipe endpoint called for recipe ID {id}")
    user_id = get_jwt_identity()
    recipe = Recipe.query.filter_by(id=id, user_id=user_id).first_or_404()
    db.session.delete(recipe)
    db.session.commit()
    logger.info(f"Deleted recipe {id} for user {user_id}")
    return jsonify({'message': 'Recipe deleted successfully'}), 200

@app.route('/analyze_image', methods=['POST'])
@jwt_required()
def analyze_image():
    """
    Analyze an image to generate a recipe for the authenticated user
    ---
    tags:
      - Recipe
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: The image to analyze
    responses:
      200:
        description: Recipe generated successfully
        schema:
          $ref: '#/definitions/Recipe'
      400:
        description: No image uploaded
    """
    logger.info("Analyze image endpoint called")
    user_id = get_jwt_identity()
    image = request.files.get('image')
    if not image:
        logger.warning("No image uploaded")
        return jsonify({'error': 'No image uploaded'}), 400

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    ingredients = recognizer.recognize(image_path)

    recipe_name, recipe_ingredients, recipe_steps = generator.generate_recipe(ingredients)

    recipe = Recipe(name=recipe_name, ingredients=f"{recipe_ingredients}\n\n{recipe_steps}", image_path=image_path, user_id=user_id)
    db.session.add(recipe)
    db.session.commit()
    logger.info(f"Generated recipe {recipe.id} for user {user_id}")
    return jsonify(recipe.as_dict())

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)