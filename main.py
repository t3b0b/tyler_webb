#region Imports
from flask import (Flask, render_template, flash,
                   request, redirect, url_for)
from flask_login import LoginManager

from models import db, User, BloggPost, Streak, Goals
from blueprints.auth import auth_bp
from blueprints.pmg import pmg_bp
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import sqlite3
import pandas as pd
# endregion

#region Appconfig

app = Flask(__name__)

app.config['SECRET_KEY'] = "K6SM4x14"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tylerobri.db"
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "pmg.automatic.services@gmail.com"
app.config['MAIL_PASSWORD'] = "gygfvycgvmjybgse"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
# Inställningar för LoginManager, som standardvy för inloggning
login_manager.login_view = 'auth.login'

db.init_app(app)
mail = Mail(app)
with app.app_context():
    db.create_all()
#endregion
def readinfo(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#region Userless
@app.route('/')
def home():
    sida="Hem"
    return render_template('home.html',sida=sida,header="Tyler O'Brien")

# endregion

#region Login/Out
app.register_blueprint(auth_bp, url_prefix='/auth')

#endregion

app.register_blueprint(pmg_bp, url_prefix='/pmg')


if __name__ == '__main__':
    app.run(debug=True)