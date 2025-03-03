import os
import sshtunnel
from flask import Flask
from dotenv import load_dotenv
from extensions import db, mail, csrf, login_manager
from blueprints.auth import auth_bp
from blueprints.pmg import pmg_bp
from blueprints.base import base_bp
from blueprints.friends import friends_bp
from blueprints.cal import cal_bp
from blueprints.txt import txt_bp
from logging.handlers import RotatingFileHandler
import logging
from flask_migrate import Migrate

def create_app():
    load_dotenv()  # Ladda miljövariabler från .env-filen
    app = Flask(__name__)

    # 🛠️ Ladda konfiguration a,dnam,dn.
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "K6SM4x14")
    app.config['MAIL_SERVER'] = "smtp.gmail.com"
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = "pmg.automatic.services@gmail.com"
    app.config['MAIL_PASSWORD'] = "gygfvycgvmjybgse"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@tylerobri.mysql.pythonanywhere-services.com/tylerobri$PMG'
    migrate = Migrate(app, db)
    
    # 🛠️ Hantera SSH-tunnel vid utveckling
    if os.getenv('FLASK_ENV') == 'development':
        tunnel = sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='tylerobri', ssh_password='Winter!sComing92',
            remote_bind_address=('tylerobri.mysql.pythonanywhere-services.com', 3306)
        )
        tunnel.start()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://tylerobri:Tellus420@127.0.0.1:{tunnel.local_bind_port}/tylerobri$PMG'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@tylerobri.mysql.pythonanywhere-services.com/tylerobri$PMG'

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

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 🛠️ Konfigurera Logging
    handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)

    # 🛠️ Skapa databastabeller om de inte finns
    with app.app_context():
        db.create_all()

    # 🛠️ Error-handler
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server Error: {error}, User: {current_user.get_id()}, Route: {request.url}, Method: {request.method}, Data: {request.data}")
        return render_template('500.html', sida='Server Fel', header='Server Fel'), 500

    return app
