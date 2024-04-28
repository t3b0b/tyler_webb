from main import app
from models import db  # anta att dina modeller och db objekt är definierade här

with app.app_context():
    db.create_all()