import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import Recipes
from PIL import Image, UnidentifiedImageError
from app import db

recipes_bp = Blueprint('recipes', __name__)

UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def resize_image(image):
    image = image.resize((500, 500))
    return image

@recipes_bp.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():

    current_chef_id = int(get_jwt_identity())

    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "Invalid input. Please provide a valid JSON object."
        }), 400

    title = data.get('title')
    description = data.get('description')
    labels = data.get('labels')

    if not isinstance(title, str) or not title.strip() or not title:
        return jsonify({
            "error": "Title is required and must be a non-empty string."
        }), 400

    if not isinstance(description, str) or not description.strip() or not description:
        return jsonify({
            "error": "Description is required and must be a non-empty string."
        }), 400

    if labels is not None and (not isinstance(labels, str) or not labels.strip()):
        return jsonify({
            "error": "Labels must be a non-empty string if provided."
        }), 400

    file = request.files.get('image')
    if not file or file.filename == '':
        return jsonify({"error": "Image file is required"}), 400

    try:
        image = Image.open(file).convert('RGB')
        image = resize_image(image) 

        safe_name = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image.save(save_path, format='JPEG', quality=85)

    except UnidentifiedImageError:
        return jsonify({"error": "Invalid image file"}), 400
    
    new_recipe = Recipes(
        title=title,
        description=description,
        labels=labels,
        image_url=f"/uploads/{unique_filename}",
        chef_id=current_chef_id
    )

    db.session.add(new_recipe)
    db.session.commit()

    return jsonify({
        "message": "Recipe created successfully",
        "recipe": {
            "id": new_recipe.id,
            "title": new_recipe.title,
            "description": new_recipe.description,
            "labels": new_recipe.labels,
            "image_url": new_recipe.image_url,
            "created_at": new_recipe.created_at.isoformat() if new_recipe.created_at else None
        }
    }), 201

@recipes_bp.route('/recipes', methods=['GET'])
@jwt_required()
def get_recipes():

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    calculate_offset = (page - 1) * limit
    total_recipes = Recipes.query.count()
    records = Recipes.query.offset(calculate_offset).limit(limit).all()

    return jsonify({
        "recipes": [
            {
                "id": recipe.id,
                "title": recipe.title,
                "description": recipe.description,
                "labels": recipe.labels,
                "image_url": recipe.image_url,
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None
            } for recipe in records
        ],
        "page": page,
        "limit": limit,
        "total": total_recipes
    }),200

