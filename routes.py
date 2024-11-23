from flask import Flask, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'din-databas-URI'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()  # Hämtar alla användare
    return jsonify([user.to_dict(exclude=["password"]) for user in users]), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)  # Returnerar 404 om användaren inte finns
    return jsonify(user.to_dict(exclude=["password"])), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        firstName=data.get('firstName', ''),
        lastName=data.get('lastName', ''),
        verified=False
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict(exclude=["password"])), 201

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        firstName=data.get('firstName', ''),
        lastName=data.get('lastName', ''),
        verified=False
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict(exclude=["password"])), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.firstName = data.get('firstName', user.firstName)
    user.lastName = data.get('lastName', user.lastName)
    if 'password' in data:
        user.password = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify(user.to_dict(exclude=["password"])), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {user_id} deleted successfully'}), 200

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request'}), 400
