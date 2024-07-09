from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_manager, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Streak, Goals, Activity, Settings, MyWords
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

auth_bp = Blueprint('auth', __name__, template_folder='auth/templates')

s = URLSafeTimedSerializer("K6SM4x14")
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from pmg import readWords
    sida = 'P.M.G'
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        skriv_goal = Goals.query.filter_by(user_id=user.id, name='Skriva').first()
        if not skriv_goal:
            skriva_goal = Goals(name="Skriva", user_id=user.id)
            db.session.add(skriva_goal)
            db.session.commit()
            skriv_goal_id = skriva_goal.id
            mina_ord = Activity(name="Mina Ord", user_id=user.id, goal_id=skriv_goal_id, unit=None)
            db.session.add(mina_ord)
            dagbok = Activity(name="Dagbok", user_id=user.id, goal_id=skriv_goal_id, unit=None)
            db.session.add(dagbok)
            bullet = Activity(name="Bullet", user_id=user.id, goal_id=skriv_goal_id, unit=None)
            db.session.add(bullet)
            db.session.commit()

            ordet, ord_lista = readWords('orden.txt')
            for ord in ord_lista:
                nyttOrd = MyWords(ord=ord, user_id=user.id)
                db.session.add(nyttOrd)
                db.session.commit()
            imported = Settings(stInterval=5, wImp=True, user_id=user.id)
            db.session.add(imported)
            db.session.commit()
        if user and check_password_hash(user.password, password):
            if not user.verified:
                flash('Kontot är inte verifierat. Kontrollera din e-post för en verifieringslänk.', 'error')
                return render_template('auth/login.html')
            login_user(user)
            today = datetime.now()
            streaks_to_reset = []

            streaks = Streak.query.all()
            for streak in streaks:
                last_reg = streak.lastReg
                reset_date = last_reg + timedelta(days=streak.interval, hours=23, minutes=59, seconds=59)

                if today > reset_date and streak.active is True:
                    streaks_to_reset.append(streak)

            if streaks_to_reset:
                session['streaks_to_reset'] = [streak.id for streak in streaks_to_reset]
                return redirect(url_for('auth.confirm_reset'))

            return redirect(url_for('pmg.myday'))
        else:
            flash('Fel användarnamn eller lösenord')
            return render_template('auth/login.html')

    return render_template('auth/login.html', sida=sida, header=sida)

@auth_bp.route('/reset', methods=['GET', 'POST'])
@login_required
def confirm_reset():
    sida = 'Nollställning'
    today_date = datetime.now()
    streak_ids = session.get('streaks_to_reset', [])
    streaks_to_reset = Streak.query.filter(Streak.id.in_(streak_ids)).all()

    if request.method == 'POST':
        checked_streaks = request.form.getlist('streak')
        for streak in streaks_to_reset:
            if str(streak.id) in checked_streaks:
                # Nollställ streaks
                streak.count = 0
                streak.active = False
            else:
                # Uppdatera streak.count för streaks som inte nollställs
                last_reg = streak.lastReg
                yesterday = datetime.now() - timedelta(days=1)
                delta_days = (yesterday - last_reg).days
                streak.count += delta_days
                streak.lastReg = yesterday
        db.session.commit()
        session.pop('streaks_to_reset', None)
        flash('Streaks har uppdaterats.', 'success')
        return redirect(url_for('pmg.myday'))
    return render_template('auth/reset.html', sida=sida, header=sida, streaks=streaks_to_reset)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from main import mail
    if request.method == 'POST':
        first = request.form.get('first-name')
        last = request.form.get('last-name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered. Please use a different email address.', 'error')
            return redirect(url_for('auth.login'))

        if not existing_user:
            hashed_password = generate_password_hash(password)
            new_user = User(firstName=first, lastName=last, username=username, password=hashed_password, email=email,verified=False)
            db.session.add(new_user)
            db.session.commit()
            token = s.dumps(email, salt='email-confirm')
            link = url_for('auth.confirm_email', token=token, _external=True)
            msg = Message('Bekräfta din e-postadress', recipients=[email], sender="pmg.automatic.services@gmail.com")
            msg.body = (f'Hej, {first} {last}! \n\n'
                        f'För att komma igång med tjänsten behöver du först aktivera ditt konto'
                        f'Detta gör du genom att klicka på länken nedan:\n{link}')
            mail.send(msg)
            flash('En e-post med en verifieringslänk har skickats till din e-postadress. Länken är giltig i 1 timme.',
                  'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))  # anta att 'main' är ett annat blueprint

@auth_bp.route('/confirm_email/<token>')
def confirm_email(token):

    try:
        email = s.loads(token, salt='email-confirm', max_age=36000)
        user = User.query.filter_by(email=email).first()

        if user:
            user.verifierad = True
            db.session.commit()

            # Skapa målet "Skriva" och aktiviteterna för den nya användaren

            return 'Din e-post har verifierats! Du kan nu logga in.'
        else:
            return '<h1>Ogiltig begäran!</h1>', 400
    except SignatureExpired:
        return '<h1>The token is expired!</h1>', 400
    except BadSignature:
        return '<h1>Ogiltig token!</h1>', 400