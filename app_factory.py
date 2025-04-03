import os
import sshtunnel
from flask import Flask, render_template,request
from flask_login import current_user
from dotenv import load_dotenv
from extensions import db, mail, csrf, login_manager
from blueprints.auth import auth_bp
from blueprints.pmg import pmg_bp
from blueprints.base import base_bp
from blueprints.friends import friends_bp
from blueprints.activities import activities_bp
from blueprints.cal import cal_bp
from blueprints.txt import txt_bp
from blueprints.streaks import streaks_bp
from blueprints.goals import goals_bp
from blueprints.tasks import tasks_bp

from logging.handlers import RotatingFileHandler
import logging
from datetime import timedelta
from flask_migrate import Migrate

def create_app():
    load_dotenv()  # Ladda miljövariabler från .env-filen
    
    app = Flask(__name__)

    # 🛠️ Ladda konfiguration a,dnam,dn.
    app.config['SECRET_KEY'] =  f'{os.getenv("SECRET_KEY")}'
    app.config['MAIL_SERVER'] = f'{os.getenv("MAIL_SERVER")}'
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
    app.config['MAIL_USERNAME'] = f'{os.getenv("MAIL_USERNAME")}'
    app.config['MAIL_PASSWORD'] = f'{os.getenv("MAIL_PASSWORD")}'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.permanent_session_lifetime = timedelta(days=2)
    migrate = Migrate(app, db)
    
    # 🛠️ Hantera SSH-tunnel vid utveckling
    if os.getenv('FLASK_ENV') == 'development':
        tunnel = sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username=os.getenv("SSH_USERNAME"), ssh_password=os.getenv("SSH_PASSWORD"),
            remote_bind_address=('tylerobri.mysql.pythonanywhere-services.com', 3306)
        )
        tunnel.start()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'{os.getenv("LOCAL_DB_URI")}{tunnel.local_bind_port}/{os.getenv("DB_NAME")}'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'{os.getenv("SQLALCHEMY_DATABASE_URI")}'

    # 🛠️ Initiera Flask-tillägg
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # 🛠️ Registrera Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pmg_bp, url_prefix='/pmg')
    app.register_blueprint(base_bp, url_prefix='/base')
    app.register_blueprint(friends_bp, url_prefix='/friends')
    app.register_blueprint(cal_bp, url_prefix='/cal')
    app.register_blueprint(txt_bp, url_prefix='/txt')
    app.register_blueprint(activities_bp,url_prefix='/activities')
    app.register_blueprint(tasks_bp,url_prefix='/tasks')
    app.register_blueprint(streaks_bp,url_prefix='/streaks')
    app.register_blueprint(goals_bp,url_prefix='/goals')

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 🛠️ Konfigurera Logging
    handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)

    # 🛠️ Skapa databastabeller om de inte finns
    with app.app_context():
        db.create_all()
    return app