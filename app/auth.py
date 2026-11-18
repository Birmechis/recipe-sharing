
import email
import re
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models import Chefs
from app import db

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,20}$")

def validate_auth(data, is_signup=True):

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "Invalid input. Please provide a valid JSON object."
        }), 400

    username = data.get('username') if is_signup else None
    email = data.get('email')
    password = data.get('password')

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Invalid input. Please provide valid string values"
        }), 400

    email = email.strip().lower()

    if not EMAIL_REGEX.match(email):
        return jsonify({
            "error": "Invalid email format. Please provide a valid email address."
        }), 400

    if not password or not password.strip():
        return jsonify({
            "error": "Invalid input. Please provide non-empty values"
        }), 400

    cleaned_data = {
        "email": email,
        "password": password
    }

    if is_signup:

          username = data.get('username')
          if not isinstance(username, str):
                return jsonify({
                    "error": "Invalid input. Please provide valid string values"
                }), 400

          username = username.strip()
          if not USERNAME_REGEX.match(username):
                return jsonify({
                    "error": "Invalid username. Please provide a valid username."
                }), 400  

          if len(password) < 8:
                return jsonify({
                    "error": "Password must be at least 8 characters long."
                }), 400
        
          if not re.search(r"[A-Za-z]", password) or not re.search(r'\d', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return jsonify({
                    "error": "Password must contain at least one letter and one number, and special character."
                }), 400

          cleaned_data["username"] = username

    return cleaned_data, None

@auth_bp.route('/signup', methods=['POST'])
def signup():

    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 415

    cleaned, error = validate_auth(request.get_json(silent=True), is_signup=True)

    if error:
        return error

    existing_chef = Chefs.query.filter_by(username=cleaned["username"], email=cleaned["email"]).first()

    if existing_chef:
        return jsonify({
            "error": "User already exists."
        }), 409

    new_chef = Chefs(
        username=cleaned["username"],
        email=cleaned["email"],
        password=generate_password_hash(cleaned["password"])
    )

    db.session.add(new_chef)
    db.session.commit()

    return jsonify({
        "message": "User created successfully."  
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 415

    cleaned, error = validate_auth(request.get_json(silent=True), is_signup=False)

    if error:
        return error

    chef = Chefs.query.filter_by(email=cleaned["email"]).first()

    if not chef:
        return jsonify({
            "error": "Invalid email or password."
        }), 401

    if not check_password_hash(chef.password, cleaned["password"]):
        return jsonify({
            "error": "Invalid email or password."
        }), 401

    token = create_access_token(identity=str(chef.id))

    return jsonify({
        "message": "Login successful.",
        "token": token
    }), 200