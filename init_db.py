from main import app
from models import db, Notes, User

with app.app_context():
    db.create_all()