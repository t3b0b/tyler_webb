from main import app
from models import db, BloggPost, User

with app.app_context():
    db.create_all()