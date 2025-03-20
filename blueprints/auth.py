import os
from extensions import mail,db
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, session)
from flask_login import (login_user, logout_user, current_user, login_required)
from werkzeug.utils import secure_filename

from pmg_func import (common_route,getInfo,filter_mod,add2db)

from werkzeug.security import generate_password_hash, check_password_hash
from models import  User, Streak, Goals, Activity, Settings, MyWords, Notification
from flask_mail import Message

from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy.orm import scoped_session
from classes.textHandler import textHandler


auth_bp = Blueprint('auth', __name__, template_folder='auth/templates')
s = URLSafeTimedSerializer("K6SM4x14")



@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)  # En funktion som skickar återställningslänk
        else:
            flash("No account found with this email.", "danger")

    return render_template('auth/reset_password.html')

def send_reset_email(user):
    token = s.dumps(user.email, salt='password-reset')
    reset_url = url_for('auth.reset_password_token', token=token, _external=True)

    msg = Message("Återställ ditt lösenord",
                  recipients=[user.email],
                  sender="pmg.automatic.services@gmail.com")

    msg.body = f"""Hej, {user.username}! 
Klicka på länken nedan för att återställa ditt lösenord:
    \n{reset_url}\n\n
(Länken är giltig i 1 timme.)"""

    try:
        mail.send(msg)
        flash("Ett återställningsmail har skickats till din e-post.", "info")
    except Exception as e:
        flash(f"Något gick fel vid skickandet av e-post: {str(e)}", "danger")

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # Token är giltig i 1 timme
    except SignatureExpired:
        flash("Länken har gått ut. Begär en ny återställning.", "danger")
        return redirect(url_for('auth.reset_password'))
    except BadSignature:
        flash("Ogiltig länk!", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Användaren hittades inte.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Lösenorden matchar inte.", "danger")
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Ditt lösenord har återställts. Logga in med det nya lösenordet.", "success")
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_token.html')

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
            streaks_to_reset = []
            streaks = Streak.query.filter_by(user_id=current_user.id).all()
            for streak in streaks:
                last_reg = streak.lastReg
                reset_date = last_reg + timedelta(days=streak.interval, hours=23, minutes=59, seconds=59)

                if today > reset_date and streak.active is True:
                    streaks_to_reset.append(streak)

            if streaks_to_reset:
                # Skicka med streaks_to_reset som en parameter i URL:en
                return redirect(url_for('auth.confirm_reset', streak_ids=[streak.id for streak in streaks_to_reset]))

            return redirect(url_for('pmg.myday'))
        else:
            flash('Fel användarnamn eller lösenord')
            return render_template('auth/login.html')

    return render_template('auth/login.html', sida=sida, header=sida)

@auth_bp.route('/reset', methods=['GET', 'POST'])
@login_required
def confirm_reset():
    sida = 'Nollställning'
    streak_ids = request.args.getlist('streak_ids')  # Hämtar streak_ids från URL:en
    user_streaks=Streak.query.filter_by(user_id=current_user.id)
    streaks_to_reset = user_streaks.filter(Streak.id.in_(streak_ids)).all()

    if request.method == 'POST':
        # Hämta alla kryssade streaks
        checked_streaks = request.form.getlist('streak')

        for streak in streaks_to_reset:
            if str(streak.id) in checked_streaks:
                # Nollställ streaken om den är kryssad
                streak.count = 0
                streak.active = False
                streak.lastReg = datetime.now()  # Uppdatera lastReg till nu
            else:
                # Om streak inte nollställs, uppdatera streak.count
                last_reg = streak.lastReg
                yesterday = datetime.now() - timedelta(days=1)
                delta_days = (yesterday - last_reg).days
                streak.count += delta_days
                streak.lastReg = yesterday

        db.session.commit()
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
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
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

            # Skapa ett grundläggande mål
            skriva_goal = Goals(name="Skriva", user_id=user.id)
            db.session.add(skriva_goal)
            db.session.flush()  # Flush för att få ID utan att committa

            # Skapa aktiviteter kopplade till målet
            aktiviteter = [
                Activity(name="Mina Ord", user_id=user.id, goal_id=skriva_goal.id),
                Activity(name="Dagbok", user_id=user.id, goal_id=skriva_goal.id),
                Activity(name="Bullet", user_id=user.id, goal_id=skriva_goal.id)
            ]
            db.session.add_all(aktiviteter)

            # Lägg till standardinställningar
            imported = Settings(stInterval=5, wImp=True, user_id=user.id)
            db.session.add(imported)

            # Slutför alla operationer i en enda commit
            db.session.commit()

            return 'Din e-post har verifierats! Du kan nu logga in.'
        else:
            return '<h1>Ogiltig begäran!</h1>', 400
    except SignatureExpired:
        return '<h1>The token is expired!</h1>', 400
    except BadSignature:
        return '<h1>Ogiltig token!</h1>', 400

# region Settings
@auth_bp.route('/settings/<section_name>', methods=['GET', 'POST'])
@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings(section_name=None):
    if not section_name:
        section_name = request.args.get('section_name', 'general')
    sida, sub_menu = common_route('Settings', [
        url_for('auth.settings', section_name='timer'),
        url_for('auth.settings', section_name='skrivande'),
        url_for('auth.settings', section_name='konto')
    ], ['Timer', 'Journal', 'Konto'])

    if section_name == 'timer':
        sida = 'Timer-inställningar'
        page_info = getInfo('pageInfo.csv', 'Time-Settings')

    elif section_name == 'skrivande':
        sida = 'Blogg-inställningar'
        page_info = getInfo('pageInfo.csv', 'Text-Settings')
        Sett = Settings.query.filter_by(user_id=current_user.id).first()


    elif section_name == 'konto':
        sida = 'Konto-inställningar'
        page_info = getInfo('pageInfo.csv', 'Account-Settings')
    else:
        sida = 'Allmänna Inställningar'
        page_info = getInfo('pageInfo.csv', 'Settings')

    mina_Ord = filter_mod(MyWords, user_id=current_user.id)

    if request.method == 'POST':
        action = request.form['action']
        if action == 'password':
            user = User.query.filter_by(id=current_user.id).first()

            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not check_password_hash(user.password, current_password):
                flash('Felaktigt nuvarande lösenord.', 'danger')
                return render_template('auth/settings.html', sida="Konto-inställningar",
                                       header="Konto-inställningar", my_words=mina_Ord,
                                       sub_menu=sub_menu, page_info=page_info, user=current_user)

            if new_password != confirm_new_password:
                flash('De nya lösenorden matchar inte.', 'danger')
                return render_template('auth/settings.html', sida="Konto-inställningar",
                                       header="Konto-inställningar", my_words=mina_Ord,
                                       sub_menu=sub_menu, page_info=page_info, user=current_user)

            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Ditt lösenord har ändrats.', 'success')
            return redirect(url_for('pmg.settings'))

        elif action == "word":
            add2db(MyWords, request, ['nytt-ord'], ['ord'], current_user)
            flash('Nytt ord har lagts till.', 'success')
            return redirect(url_for('pmg.settings', section_name=section_name))

        elif action == "timer":
            existing_setting = Settings.query.filter_by(user_id=current_user.id).first()
            intervall = request.form.get('time-intervall')
            if existing_setting:
                existing_setting.stInterval = int(intervall)
                flash('Timer-inställningar har uppdaterats.', 'success')

        elif action == 'delete_word':
            word_id = request.form.get('delete_word')
            word_to_delete = MyWords.query.filter_by(id=word_id).first()
            if word_to_delete and word_to_delete.user_id == current_user.id:
                db.session.delete(word_to_delete)
                db.session.commit()
            return render_template('auth/settings.html', sida=sida, header=sida, my_words=mina_Ord,
                                   sub_menu=sub_menu, page_info=page_info, user=current_user)

    return render_template('auth/settings.html', sida=sida, header=sida, my_words=mina_Ord,
                           sub_menu=sub_menu, page_info=page_info, user=current_user)

@auth_bp.route('/profile')
@login_required
def profile():
    uID = current_user.id
    my_user = User.query.filter_by(id=uID).first()
    notifications = Notification.query.filter_by(user_id=my_user.id).order_by(Notification.created_at.desc()).all()
    print(my_user)

    sida, sub_menu = common_route(f'{my_user.firstName} {my_user.lastName}', ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks','Goals','Milestones'])
    return render_template('auth/profile.html', user=my_user, sida = sida, header=sida, notifications=notifications)

@auth_bp.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    from main import app  # Säkerställ att du importerar app-konfiguration

    # Definiera tillåtna filtyper om det inte redan är gjort
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    UPLOAD_FOLDER = 'static/uploads'  # Sökväg för att spara filer
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    me = User.query.filter_by(id=current_user.id).first()
    # Kontrollera om filen finns i requesten
    if 'profile-pic' not in request.files:
        flash('Ingen fil valdes.', 'error')
        return redirect(url_for('auth.profile'))

    file = request.files['profile-pic']

    # Kontrollera om filnamnet inte är tomt
    if file.filename == '':
        flash('Ingen fil valdes.', 'error')
        return redirect(url_for('auth.profile'))

    # Kontrollera filtyp
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash('Filtypen är inte tillåten. Använd PNG, JPG, JPEG eller GIF.', 'error')
        return redirect(url_for('auth.profile'))

    # Säkra filnamnet och spara filen
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Uppdatera användarens profilbild i databasen
    current_user.profilePic = filename
    db.session.commit()

    flash('Profilbilden har laddats upp framgångsrikt!', 'success')
    return redirect(url_for('auth.profile'))

# endregion