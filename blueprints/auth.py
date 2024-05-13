from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_manager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

auth_bp = Blueprint('auth', __name__, template_folder='templates')

s = URLSafeTimedSerializer("K6SM4x14")
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('pmg.month'))  # Antag att 'month' är korrekt definierad i din Flask app
        else:
            flash('Fel användarnamn eller lösenord')
            return render_template('login.html')  # Se till att returnera templaten även här
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from main import mail
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form['email']
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        token = s.dumps(email, salt='email-confirm')
        # Skapa en verifieringslänk

        link = url_for('auth.confirm_email', token=token, _external=True)
        msg = Message('Bekräfta din e-postadress', recipients=[email], sender="pmg.automatic.services@gmail.com")
        msg.body = f'Din länk för att verifiera din e-post är {link}'
        mail.send(msg)
        return 'En e-post med en verifieringslänk har skickats till din e-postadress. Länken är giltig i 1 timme.'
        return redirect(url_for('auth.login'))
        pass
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))  # anta att 'main' är ett annat blueprint

@auth_bp.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        användaren = User.query.filter_by(email=email).first()
        if användaren:
            användaren.verifierad = True
            db.session.commit()
            return 'Din e-post har verifierats!'
        else:
            return '<h1>Ogiltig begäran!</h1>', 400
    except SignatureExpired:
        return '<h1>The token is expired!</h1>', 400
    except BadSignature:
        return '<h1>Ogiltig token!</h1>', 400