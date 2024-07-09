#region Imports
from flask import (Flask, render_template, flash,
                   request, redirect, url_for)
from flask_login import LoginManager
from blueprints.friends import friends_bp
from blueprints.base import base_bp,read_info
from models import db, User, BloggPost, Streak, Goals, MyWords
from blueprints.auth import auth_bp
from blueprints.pmg import pmg_bp
from flask_mail import Mail, Message
import os
import mysql.connector

# endregion

#region Appconfig

app = Flask(__name__)
app.config['SECRET_KEY'] = "K6SM4x14"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Tellus420@localhost/pmgonline'
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "pmg.automatic.services@gmail.com"
app.config['MAIL_PASSWORD'] = "gygfvycgvmjybgse"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

#mysql.connector.connect(host="localhost",user="root",password="Tellus420",database="Tellus420")
app.register_blueprint(pmg_bp, url_prefix='/pmg')
app.register_blueprint(base_bp, url_prefix='/base')
app.register_blueprint(friends_bp, url_prefix='/friends')

db.init_app(app)
mail = Mail(app)
with app.app_context():
    db.create_all()

#endregion
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#region Userless
@app.route('/')
def home():
    sida = "Hem"
    info = read_info("texts/unikOrg.txt")
    unik = info.split("*")
    content_header = [unik[i] for i in range(len(unik)) if i % 2 == 0]
    content_text = [unik[i] for i in range(len(unik)) if i % 2 != 0]
    start_info = zip(content_header, content_text)
    return render_template('base/home.html',sida=sida,header="Tyler O'Brien",sideOptions=None, start_info=start_info)
@app.route('/blog')
def blog():
    sida="Blogg"
    render_template('blog.html',sida=sida,header=sida,)
# endregion

#region Login/Out
app.register_blueprint(auth_bp, url_prefix='/auth')

#endregion



if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5001,debug=True)