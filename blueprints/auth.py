from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_manager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Streak, Goals, Activity, Settings
from flask_mail import Mail, Message
from datetime import datetime,timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

auth_bp = Blueprint('auth', __name__, template_folder='auth/templates')

s = URLSafeTimedSerializer("K6SM4x14")
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    sida = 'P.M.G'
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if not user.verified:
                flash('Kontot är inte verifierat. Kontrollera din e-post för en verifieringslänk.', 'error')
                return render_template('auth/login.html')
            login_user(user)
            today = datetime.now()
            streaks = Streak.query.all()

            for streak in streaks:
                last_reg = datetime.strptime(streak.lastReg, "%Y-%m-%d")
                reset_date = (last_reg + timedelta(days=streak.interval, hours=23, minutes=59,
                                                   seconds=59))  # Konvertera till datum
                print(f'{streak.name} - {reset_date} - {today}')
                if today > reset_date:
                    streak.count = 0
                    streak.active = False  # Exempel: sätt streak till inaktiv om den nollställs
                    db.session.commit()
            return redirect(url_for('pmg.myday'))  # Antag att 'month' är korrekt definierad i din Flask app
        else:
            flash('Fel användarnamn eller lösenord')
            return render_template('auth/login.html')  # Se till att returnera templaten även här

    return render_template('auth/login.html',sida=sida,header=sida)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from main import mail

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered. Please use a different email address.', 'error')
            return redirect(url_for('auth.login'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        token = s.dumps(email, salt='email-confirm')
        link = url_for('auth.confirm_email', token=token, _external=True)
        msg = Message('Bekräfta din e-postadress', recipients=[email], sender="pmg.automatic.services@gmail.com")
        msg.body = (f'Hej, {username}\n'
                    f'Din länk för att verifiera din e-post är {link}')
        mail.send(msg)

        # Skapa målet "Skriva" och aktiviteterna för den nya användaren
        skriva_goal = Goals(name="Skriva", user_id=new_user.id)
        db.session.add(skriva_goal)
        db.session.commit()

        skriv_goal_id = skriva_goal.id
        mina_ord = Activity(name="Mina Ord", user_id=new_user.id, goal_id=skriv_goal_id, measurement="Tid")
        db.session.add(mina_ord)
        dagbok = Activity(name="Dagbok", user_id=new_user.id, goal_id=skriv_goal_id, measurement="Tid")
        db.session.add(dagbok)
        stand_int = Settings(user_id=new_user.id, stInterval=5)
        db.session.add(stand_int)
        db.session.commit()

        return 'En e-post med en verifieringslänk har skickats till din e-postadress. Länken är giltig i 1 timme.'

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))  # anta att 'main' är ett annat blueprint

@auth_bp.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.verifierad = True
            db.session.commit()
            return 'Din e-post har verifierats! Du kan nu logga in.'
        else:
            return '<h1>Ogiltig begäran!</h1>', 400
    except SignatureExpired:
        return '<h1>The token is expired!</h1>', 400
    except BadSignature:
        return '<h1>Ogiltig token!</h1>', 400