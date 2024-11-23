#region Imports
import logging
from logging.handlers import RotatingFileHandler
from flask import (Flask, render_template, flash,
                   request, redirect, url_for, session)
from pmg_func import delete_old_notifications
from flask_login import LoginManager, current_user
from blueprints.friends import friends_bp
from blueprints.base import base_bp,read_info
from models import db, User, Notes, Streak, Goals, MyWords
from blueprints.auth import auth_bp
from blueprints.pmg import pmg_bp
from blueprints.cal import cal_bp
from blueprints.txt import txt_bp
from flask_mail import Mail, Message
from flask_wtf import CSRFProtect

from flask_migrate import Migrate,migrate,init
import sshtunnel
import os
from dotenv import load_dotenv
# endregion


#region Appconfig

load_dotenv()  # Ladda miljövariabler från .env-filen
app = Flask(__name__)


if os.getenv('FLASK_ENV') == 'development':
    tunnel = sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'), ssh_username='tylerobri', ssh_password='Winter!sComing92',
        remote_bind_address=('tylerobri.mysql.pythonanywhere-services.com', 3306)
    )
    tunnel.start()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@127.0.0.1:{}/tylerobri$PMG'.format(tunnel.local_bind_port)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@tylerobri.mysql.pythonanywhere-services.com/tylerobri$PMG'

app.config['SECRET_KEY'] = "K6SM4x14"
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "pmg.automatic.services@gmail.com"
app.config['MAIL_PASSWORD'] = "gygfvycgvmjybgse"
app.config[('SQLALCHEMY_TRACK_MODIFICATI.- )'
            'ONS')] = False

csrf = CSRFProtect(app)
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

#region blueprints
app.register_blueprint(pmg_bp, url_prefix='/pmg')
app.register_blueprint(base_bp, url_prefix='/base')
app.register_blueprint(friends_bp, url_prefix='/friends')
app.register_blueprint(cal_bp, url_prefix='/cal')
app.register_blueprint(txt_bp, url_prefix='/txt')

# endregion

mail = Mail(app)
db.init_app(app)

with app.app_context():
    db.create_all()
#endregion

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}, User: {current_user.get_id()}, Route: {request.url}, "
                     f"Method: {request.method}, Data: {request.data}")
    return render_template('500.html',sida='Server Fel',header='Server Fel'), 500

# Exempelrutt som kan orsaka ett fel
@app.route('/cause_error')
def cause_error():
    raise Exception("This is a test exception")

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
    app.run(host="0.0.0.0",port=5001, debug=True)