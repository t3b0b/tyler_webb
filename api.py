from flask import Flask, request, jsonify
from models import db, User, Notes, Goals
import sshtunnel
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

if os.getenv('FLASK_ENV') == 'development':
    tunnel = sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'), ssh_username='tylerobri', ssh_password='Winter!sComing92',
        remote_bind_address=('tylerobri.mysql.pythonanywhere-services.com', 3306)
    )
    tunnel.start()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@127.0.0.1:{}/tylerobri$PMG'.format(tunnel.local_bind_port)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])  # to_dict() skapas i modellerna
    elif request.method == 'POST':
        data = request.json
        new_user = User(username=data['username'], email=data['email'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'GET':
        return jsonify(user.to_dict())
    elif request.method == 'PUT':
        data = request.json
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.password = data.get('password', user.password)
        db.session.commit()
        return jsonify(user.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return '', 204

@app.route('/api/notes', methods=['GET', 'POST'])
def handle_notes():
    if request.method == 'GET':
        notes = Notes.query.all()
        return jsonify([note.to_dict() for note in notes])
    elif request.method == 'POST':
        data = request.json
        new_note = Notes(title=data['title'], content=data['content'], user_id=data['user_id'])
        db.session.add(new_note)
        db.session.commit()
        return jsonify(new_note.to_dict()), 201

@app.route('/api/notes/<int:note_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_note(note_id):
    note = Notes.query.get_or_404(note_id)
    if request.method == 'GET':
        return jsonify(note.to_dict())
    elif request.method == 'PUT':
        data = request.json
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        db.session.commit()
        return jsonify(note.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(note)
        db.session.commit()
        return '', 204

@app.route('/api/goals', methods=['GET', 'POST'])
def handle_goals():
    if request.method == 'GET':
        goals = Goals.query.all()
        return jsonify([goal.to_dict() for goal in goals])
    elif request.method == 'POST':
        data = request.json
        new_goal = Goals(title=data['title'], description=data['description'], user_id=data['user_id'])
        db.session.add(new_goal)
        db.session.commit()
        return jsonify(new_goal.to_dict()), 201

@app.route('/api/goals/<int:goal_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_goal(goal_id):
    goal = Goals.query.get_or_404(goal_id)
    if request.method == 'GET':
        return jsonify(goal.to_dict())
    elif request.method == 'PUT':
        data = request.json
        goal.title = data.get('title', goal.title)
        goal.description = data.get('description', goal.description)
        db.session.commit()
        return jsonify(goal.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(goal)
        db.session.commit()
        return '', 204

if __name__ == '__main__':
    app.run(debug=True)
