from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from models import (User, db, Streak, Goals, Friendship, Notes, SharedItem, ActivityTracking, Notification,
                    Activity, Score, Dagar, ToDoList, TopFive, SubTask)
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta, date
from sqlalchemy import and_
from pmg_func import (getInfo, common_route, add2db, unique,
                      section_content, update_dagar, completed_streaks,
                      update_streak_details, myDayScore,
                      generate_calendar_weeks, filter_mod, create_notification)
import pandas as pd
from pytz import timezone
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import scoped_session

pmg_bp = Blueprint('pmg', __name__, template_folder='templates/pmg')

Questions = {
    "priorities": "Vad är viktigt för dig att prioritera idag?",
    "tacksam": "Vad har du att vara tacksam för?",
    "tankar": "Vilka tankar/insikter vill du påminna dig själv om?",
    "bättre": "Vad ska du se till att göra bättre idag?",
    "känslor": "Hur känner du dig just nu, och varför?",
    "mål": "Vilka mål vill du nå idag?",
    "relationer": "Finns det någon du vill ge extra uppmärksamhet till idag?",
    "lärande": "Vad vill du lära dig eller utforska idag?",
    "hälsa": "Vad kan du göra idag för att ta hand om din hälsa och energi?",
    "uppskattning": "Vad eller vem kan du visa uppskattning för idag?",
    "kreativitet": "Hur kan du uttrycka din kreativitet idag?",
    "utmaningar": "Finns det någon utmaning du kan ta itu med idag?",
    "avslappning": "Vad kan du göra för att slappna av och återhämta dig idag?",
    "för_imorgon": "Vad kan du göra idag för att underlätta morgondagen?",
}
def create_streak_notification(streak, message):
    participants = SharedStreak.query.filter_by(streak_id=streak.id, status='active').all()
    for participant in participants:
        if participant.user_id != current_user.id:
            create_notification(
                user_id=participant.user_id,
                message=message,
                related_item_id=streak.id,
                item_type='streak'
            )

def notify_streak_status(streak_id):
    shared_items = SharedItem.query.filter_by(item_type='streak', item_id=streak_id, status='active').all()

    for shared_item in shared_items:
        if shared_item.shared_with_id != current_user.id:
            create_notification(
                user_id=shared_item.shared_with_id,
                message=f"{current_user.username} behöver hjälp med streak: {shared_item.streak.name}.",
                related_item_id=shared_item.item_id,
                item_type='streak'
            )

def SortStreaks(Streaks):
    valid_streaks = []
    now = datetime.now()
    for streak in Streaks:
        interval_days = timedelta(days=streak.interval, hours=23, minutes=59, seconds=59)
        if streak.lastReg:
            try:
                last_reg_date = streak.lastReg
                streak_interval = last_reg_date + interval_days
                if streak.count == 0:
                    valid_streaks.append(streak)
                elif streak.count >= 1:
                    if now.date() == streak_interval.date():
                        valid_streaks.append(streak)
                    elif streak_interval.date() < now.date():
                        continue
                elif streak_interval.date() < now.date():
                    streak.active = False
                    streak.count = 0
                    db.session.commit()
            except (ValueError, TypeError) as e:
                print(f'Hantera ogiltigt datum: {e}, streak ID: {streak.id}, lastReg: {streak.lastReg}')
        else:
            valid_streaks.append(streak)
    return valid_streaks

def get_weekly_scores(user_id):
    today = datetime.utcnow()
    start_of_this_week = today - timedelta(days=today.weekday())
    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(days=1)

    # Hämta poäng från databasen
    this_week_scores = db.session.query(
        Score.Date, db.func.sum(Score.Time).label('total_points')
    ).filter(
        Score.user_id == user_id,
        Score.Date >= start_of_this_week,
        Score.Date <= today
    ).group_by(Score.Date).all()

    last_week_scores = db.session.query(
        Score.Date, db.func.sum(Score.Time).label('total_points')
    ).filter(
        Score.user_id == user_id,
        Score.Date >= start_of_last_week,
        Score.Date <= end_of_last_week
    ).group_by(Score.Date).all()

    return this_week_scores, last_week_scores

def create_week_comparison_plot(this_week_scores, last_week_scores):
    days = ['Mån', 'Tis', 'Ons', 'Tors', 'Fre', 'Lör', 'Sön']
    x = range(len(days))

    # Konvertera datan till en form som passar grafer
    this_week_data = {score.Date.weekday(): score.total_points for score in this_week_scores}
    last_week_data = {score.Date.weekday(): score.total_points for score in last_week_scores}

    this_week = [this_week_data.get(i, 0) for i in range(7)]
    last_week = [last_week_data.get(i, 0) for i in range(7)]

    plt.figure(figsize=(10, 6))
    plt.bar(x, last_week, alpha=0.2, label="Föregående vecka", color="blue",)
    plt.bar(x, this_week, alpha=0.6, label="Aktuell vecka", color="orange")
    plt.xticks(x, days, fontsize=14)
#    plt.ylabel("Score")
    plt.ylim(15, 350)  # Sätter y-axeln från 15 till 350
    plt.yticks(range(0, 360, 30), fontsize=14)
    plt.legend(fontsize=14)
    plt.tight_layout(pad=2.0)
    plt.grid(color='lightgray', linestyle='--', linewidth=0.5)  # Ställ in rutnätets stil och färg

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

def get_activities_for_goal(user_id, goal_id):
    # Kontrollera om målet finns bland användarens tillåtna mål
    all_goals = get_user_goals(user_id)
    allowed_goal_ids = [goal.id for goal in all_goals]

    if goal_id not in allowed_goal_ids:
        raise ValueError("Användaren har inte tillgång till detta mål.")

    # Hämta aktiviteter kopplade till det specifika målet
    return Activity.query.filter_by(goal_id=goal_id).all()

def get_user_goals(user_id):
    # Hämta användarens egna mål
    own_goals = Goals.query.filter_by(user_id=user_id).all()

    # Hämta delade mål via SharedItem
    shared_goal_ids = db.session.query(SharedItem.item_id).filter(
        SharedItem.shared_with_id == user_id,
        SharedItem.item_type == 'goal',
        SharedItem.status == 'accepted'  # Endast accepterade mål
    ).all()

    # Konvertera shared_goal_ids till en lista av ID:n
    shared_goal_ids = [item[0] for item in shared_goal_ids]

    # Hämta själva målen från deras ID:n
    shared_goals = Goals.query.filter(Goals.id.in_(shared_goal_ids)).all()

    # Kombinera egna och delade mål
    return own_goals + shared_goals

def get_user_tasks(user_id,  model, activity_id=None):

    # Hämta alla aktiviteter som användaren har tillgång till
    all_activities = model.query.filter_by(user_id=user_id).all()

    activity_ids = [activity.id for activity in all_activities]

    # Om activity_id anges, filtrera på den specifika aktiviteten
    query = ToDoList.query.filter(ToDoList.activity_id.in_(activity_ids))
    if activity_id:
        query = query.filter(ToDoList.activity_id == activity_id)

    # Sortera tasks (avklarade först, sedan alfabetiskt)
    return query.options(db.joinedload(ToDoList.subtasks)).order_by(ToDoList.completed.desc(), ToDoList.task.asc()).all()

def get_daily_scores(user_id):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Hämta poäng för idag och igår
    today_score = Score.query.filter_by(user_id=user_id, date=today).first()
    yesterday_score = Score.query.filter_by(user_id=user_id, date=yesterday).first()

    if today_score and yesterday_score:
        if today_score > yesterday_score:
            message = "Bra jobbat! Du har överträffat din poäng från igår."
        else:
            message = "Försök få en högre poäng imorgon!"
    elif today_score:
        message = "Bra start idag!"
    else:
        message = "Inga poäng registrerade för idag ännu."

    return today_score, yesterday_score, message

def get_today_score(user_id):
    """Hämta dagens score för en specifik användare."""
    today = datetime.now().date()
    today_score = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == today
    ).scalar() or 0
    return today_score

def get_yesterday_score(user_id):
    """Hämta gårdagens score för en specifik användare."""
    yesterday = datetime.now().date() - timedelta(days=1)
    yesterday_score = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == yesterday
    ).scalar() or 0
    return yesterday_score

def get_week_activity_times(user_id):
    """Hämta total tid per aktivitet under aktuell vecka för en specifik användare."""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Måndag i denna vecka
    end_of_week = start_of_week + timedelta(days=6)  # Söndag i denna vecka

    activity_times = db.session.query(
        Activity.name,
        db.func.sum(Score.Time).label('total_time')
    ).join(Score).filter(
        Score.user_id == user_id,
        Score.Date.between(start_of_week, end_of_week)
    ).group_by(Activity.name).all()

    return activity_times

def create_activity_plot(activity_times):
    """Generera en stående stapelgraf med unika färger för varje mål."""
    activity_names = [activity[0] for activity in activity_times]
    total_times = [activity[1] for activity in activity_times]

    # Färger för varje stapel, genereras automatiskt för att vara unika
    colors = plt.cm.get_cmap('tab20', len(activity_names))(range(len(activity_names)))
    plt.figure(figsize=(10, 8),facecolor='none', edgecolor='k',)
    plt.bar(activity_names, total_times, color=colors)  # Stående staplar
    plt.ylabel('Total Tid (min)',fontsize=10)
    plt.xlabel('Aktivitet', fontsize=10)
    plt.xticks(rotation=0, ha='center',fontsize=14)
    plt.yticks(rotation=0, ha='right',fontsize=14)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    # Konvertera bilden till base64 för att inkludera den i HTML
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return plot_url

def update_shared_streak(streak_id, completed=True):
    shared_items = SharedItem.query.filter_by(item_type='streak', item_id=streak_id, status='active').all()

    for shared_item in shared_items:
        streak = shared_item.streak
        if completed:
            streak.count += 1
        else:
            streak.count = 0
        db.session.commit()

        # Notifiera deltagarna
        if shared_item.shared_with_id != current_user.id:
            create_notification(
                user_id=shared_item.shared_with_id,
                message=f"{current_user.username} uppdaterade streak: {streak.name}.",
                related_item_id=streak.id,
                item_type='streak'
            )

def challenge_user_to_streak(streak_id, friend_id):
    original_streak = Streak.query.get(streak_id)
    if not original_streak:
        raise ValueError("Ogiltig streak.")

    # Kontrollera att användaren är en vän
    friendship = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend_id, status='accepted').first()
    if not friendship:
        raise ValueError("Användaren är inte din vän.")

    new_streak = Streak(
        name=f"Utmaning: {original_streak.name}",
        user_id=friend_id,
        interval=original_streak.interval,
        count=0
    )
    db.session.add(new_streak)
    db.session.commit()

    create_notification(
        user_id=friend_id,
        message=f"{current_user.username} har utmanat dig med streak: '{original_streak.name}'.",
        related_item_id=new_streak.id,
        item_type='streak'
    )


@pmg_bp.route('/notifications/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': notification.id,
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications])


@pmg_bp.route('/notifications/mark_as_read', methods=['POST'])
@login_required
def mark_notifications_as_read():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'})


#region Streak
@pmg_bp.route('/streak',methods=['GET', 'POST'])
@login_required
def streak():
    current_date = date.today()
    current_date = current_date.strftime('%Y-%m-%d')
    sida, sub_menu = common_route("Mina Streaks", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks','Goals','Milestones'])
    myStreaks = filter_mod(Streak,user_id=current_user.id)
    myGoals = filter_mod(Goals, user_id=current_user.id)

    if request.method == 'POST':
        form_fields = ['streakName','streakInterval','streakCount',
                       'streakType','goalSelect','streakBest',
                       'streakCondition','streakLast','streakStart']
        model_fields = ['name', 'interval', 'count', 'type',
                        'goal_id','best','condition',
                        'lastReg','dayOne']
        add2db(Streak, request, form_fields, model_fields, current_user)

        return redirect(url_for('pmg.streak'))
    return render_template('pmg/streak.html',sida=sida,header=sida,
                           todayDate=current_date,streaks=myStreaks,sub_menu=sub_menu,
                       goals=myGoals)

@pmg_bp.route('/streak/<int:shared_streak_id>/respond', methods=['POST'])
@login_required
def respond_to_streak_invitation(shared_streak_id):
    shared_streak = SharedStreak.query.get_or_404(shared_streak_id)

    if shared_streak.user_id != current_user.id:
        flash("Du har inte rätt att svara på denna inbjudan.", "danger")
        return redirect(url_for('pmg.streak'))

    action = request.form.get('action')
    if action == 'accept':
        shared_streak.status = 'active'
        create_notification(
            user_id=shared_streak.owner_id,
            message=f"{current_user.username} har accepterat streak-inbjudan!",
            related_item_id=shared_streak.id,
            item_type='streak'
        )
        flash("Du har accepterat inbjudan!", "success")
    elif action == 'decline':
        shared_streak.status = 'declined'
        create_notification(
            user_id=shared_streak.owner_id,
            message=f"{current_user.username} har avböjt streak-inbjudan.",
            related_item_id=shared_streak.id,
            item_type='streak'
        )
        flash("Du har avböjt inbjudan.", "info")

    db.session.commit()
    return redirect(url_for('pmg.streak'))

@pmg_bp.route('/streak/<int:streak_id>/details', methods=['GET'])
def streak_details(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    streakdetail = Streak.query.filter_by(user_id=current_user.id, id = streak_id).first()

    return render_template('pmg/details.html', streak=streak, detail=streakdetail)

@pmg_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = date.today()
    midnight_today = datetime.combine(today, datetime.min.time())  # Sätter tiden till 00:00:00
    current_date = today.strftime('%Y-%m-%d')

    if action == 'check':
        score, goal_id = update_streak_details(streak, midnight_today)
        flash(f"Score: {score}, Goal ID: {goal_id}")  # Lägg till denna rad för felsökning

        # Kontrollera att goal_id och score har giltiga värden
        if goal_id and score:
            new_score = Score(Goal=goal_id, Activity=None, Time=score, Date=current_date, user_id=current_user.id)
            db.session.add(new_score)
            db.session.commit()
            print("New score added successfully")  # Lägg till denna rad för felsökning
        else:
            print("Invalid goal_id or score")  # Lägg till denna rad för felsökning

    elif action == 'cross':
        streak.count = 0
        streak.active = False
        streak.dayOne = today  # Reset the start day of the streak
        streak.lastReg = today
        streak.level = 1  # Återställ nivån till 1
        update_dagar(current_user, Dagar)
        db.session.commit()
        print("Streak reset")  # Lägg till denna rad för felsökning

    update_dagar(current_user.id, Dagar)

    return redirect(url_for('pmg.myday'))

@pmg_bp.route('/delete-streak/<int:streak_id>', methods=['POST'])
def delete_streak(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    if streak.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(streak)
    db.session.commit()
    return jsonify({'success': True})
# endregion

#region Goals
@pmg_bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    sida, sub_menu = common_route("Mina Mål", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'],
                                  ['Streaks', 'Goals', 'Milestones'])
    start_activity = request.args.get('start_activity', None)

    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            goal_name = request.form.get('goalName')
            friend_id = request.form.get('friend_id')
            print(friend_id)

            if friend_id == "none":
                # Skapa ett nytt mål för den inloggade användaren
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
            else:
                # Skapa målet först
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
                db.session.flush()  # Få mål-ID utan att committa

                # Skapa SharedItem-poster för både skaparen och vännen
                shared_goal_user = SharedItem(
                    item_type='goal',
                    item_id=new_goal.id,
                    owner_id=current_user.id,
                    shared_with_id=current_user.id,
                    status='accepted'
                )
                shared_goal_friend = SharedItem(
                    item_type='goal',
                    item_id=new_goal.id,
                    owner_id=current_user.id,
                    shared_with_id=friend_id,
                    status='pending'
                )
                db.session.add_all([shared_goal_user, shared_goal_friend])

                # Skapa en notifikation för vännen
                create_notification(
                    user_id=friend_id,
                    message=f"{current_user.username} has invited you to share the goal: '{goal_name}'.",
                    related_item_id=new_goal.id,
                    item_type='goal'
                )

            db.session.commit()  # Slutför allt i en transaktion

        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = ToDoList(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            return redirect(url_for('pmg.goals'))

    # Hämta mål på nytt varje gång sidan laddas för att säkerställa att listan är uppdaterad
    personal_goals = Goals.query.filter(
        Goals.user_id == current_user.id,  # Mål som tillhör nuvarande användare
        ~Goals.id.in_(db.session.query(SharedItem.item_id).filter(
            SharedItem.item_type == 'goal'  # Endast SharedItems kopplade till mål
        ))
    ).all()

    # Hämta alla mål som antingen skapats av användaren eller som användaren har blivit inbjuden till och accepterat
    shared_goals = db.session.query(Goals).select_from(Goals).join(
        SharedItem,
        and_(
            SharedItem.item_id == Goals.id,  # Kopplar mål med SharedItem baserat på item_id
            SharedItem.item_type == 'goal'  # Ser till att det är mål som delas
        )
    ).filter(
        (Goals.user_id == current_user.id) |  # Mål skapade av användaren
        ((SharedItem.shared_with_id == current_user.id) & (SharedItem.status == 'accepted'))  # Accepterade inbjudningar
    ).all()

    # Hämta mottagna mål-förfrågningar som ännu inte accepterats
    received_requests = db.session.query(
        SharedItem.id.label('request_id'),  # ID för förfrågan
        Goals.name.label('goal_title'),  # Målets namn
        User.username.label('created_by')  # Skaparen av målet
    ).join(
        Goals, SharedItem.item_id == Goals.id
    ).join(
        User, Goals.user_id == User.id
    ).filter(
        SharedItem.shared_with_id == current_user.id,  # Förfrågningar till den inloggade användaren
        SharedItem.status == 'pending',  # Endast ej accepterade förfrågningar
        SharedItem.item_type == 'goal'  # Endast för mål
    ).all()

    # Hämta skickade mål-förfrågningar som ännu inte accepterats
    sent_requests = db.session.query(
        SharedItem.id.label('request_id'),  # ID för förfrågan
        Goals.name.label('goal_title'),  # Målets namn
        User.username.label('sent_to')  # Mottagaren av förfrågan
    ).join(
        Goals, SharedItem.item_id == Goals.id
    ).join(
        User, SharedItem.shared_with_id == User.id
    ).filter(
        SharedItem.owner_id == current_user.id,  # Förfrågningar från den inloggade användaren
        SharedItem.status == 'pending',  # Endast ej accepterade förfrågningar
        SharedItem.item_type == 'goal'  # Endast för mål
    ).all()

    # Hämta vänner för att kunna dela mål
    accepted_friends = Friendship.query.filter_by(user_id=current_user.id, status='accepted').all() + \
                       Friendship.query.filter_by(friend_id=current_user.id, status='accepted').all()
    accepted_user_ids = [friend.user_id if friend.user_id != current_user.id else friend.friend_id for friend in
                         accepted_friends]
    friends = User.query.filter(User.id.in_(accepted_user_ids)).all()

    return render_template('pmg/goals.html',
                           received_requests=received_requests,
                           sent_requests=sent_requests,
                           sida=sida,
                           header=sida,
                           personal_goals=personal_goals,
                           sub_menu=sub_menu,
                           friends=friends,
                           shared_goals=shared_goals,
                           start_activity=start_activity)

@pmg_bp.route('/goal_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def handle_goal_request(request_id, action):
    # Hämta SharedItem med ID och säkerställ att det är av typen "goal"
    shared_item = SharedItem.query.get_or_404(request_id)

    # Verifiera att det delade objektet är ett mål
    if shared_item.item_type != 'goal':
        flash("Ogiltig förfrågan: Objektet är inte ett mål.", 'danger')
        return redirect(url_for('pmg.goals'))

    # Kontrollera att användaren har behörighet att hantera förfrågan
    if shared_item.shared_with_id != current_user.id:
        flash("Du har inte behörighet att hantera denna förfrågan.", 'danger')
        return redirect(url_for('pmg.goals'))

    # Hantera olika åtgärder
    if action == 'accept':
        shared_item.status = 'accepted'
        flash("Målet har accepterats!", 'success')
    elif action == 'decline':
        db.session.delete(shared_item)
        flash("Mål-förfrågan har avböjts.", 'info')

    # Spara ändringarna
    db.session.commit()
    return redirect(url_for('pmg.goals'))

@pmg_bp.route('/goal/<int:goal_id>/activities', methods=['GET', 'POST'])
def goal_activities(goal_id):
    goal = Goals.query.get_or_404(goal_id)
    user = current_user.id
    shared_item = SharedItem.query.filter_by(item_id=goal_id, item_type='goal', status='active').first()
    start_activity = request.args.get('start_activity', None)

    if request.method == 'POST':
        # Hantera POST-begäran för att lägga till en aktivitet
        goalId = goal_id
        activity_name = request.form.get('activity-name')
        measurement = request.form.get('activity-measurement')

        if activity_name and measurement:
            # Skapa aktivitet
            new_activity = Activity(
                name=activity_name,
                goal_id=goal.id,
                user_id=user,
                shared_item_id=shared_item.id if shared_item else None  # Koppla till delning om målet är delat
            )
            db.session.add(new_activity)
            db.session.commit()

            if shared_item:
                # Hämta alla användare som målet är delat med
                shared_users = SharedItem.query.filter_by(item_id=goal_id, item_type='goal', status='active').all()
                for shared_user in shared_users:
                    if shared_user.shared_with_id != current_user.id:  # Hoppa över nuvarande användare
                        create_notification(
                            user_id=shared_user.shared_with_id,  # Mottagarens ID
                            message=f"{current_user.username} created a new activity '{activity_name}' in goal '{goal.name}'.",
                            related_item_id=new_activity.id,
                            item_type='activity'
                        )

            flash('Activity added successfully', 'success')
            return redirect(url_for('pmg.goal_activities', goal_id=goal_id))
        else:
            flash('Activity name and measurement are required', 'danger')

    # Hantera GET-begäran för att visa aktiviteterna
    activities = Activity.query.filter_by(goal_id=goal_id).all()
    return render_template('pmg/activities.html', goal=goal, start_activity=start_activity ,activities=activities)

@pmg_bp.route('/goal/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goals.query.get_or_404(goal_id)

    # Kontrollera att användaren äger målet
    if goal.user_id != current_user.id:
        flash("Du har inte behörighet att ta bort detta mål.", "danger")
        return redirect(url_for('pmg.goals'))

    try:
        # Radera relaterade aktiviteter och tasks
        for activity in goal.activities:
            # Ta bort relaterade tasks
            ToDoList.query.filter_by(activity_id=activity.id).delete()

            # Ta bort relaterade notes
            Notes.query.filter_by(activity_id=activity.id).delete()

            # Ta bort själva aktiviteten
            db.session.delete(activity)

        # Ta bort milstolpar
        for milestone in goal.milestones:
            db.session.delete(milestone)

        # Ta bort delade objekt
        SharedItem.query.filter_by(item_type='goal', item_id=goal.id).delete()

        # Radera själva målet
        db.session.delete(goal)
        db.session.commit()

        flash("Målet har tagits bort.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('pmg.goals'))



@pmg_bp.route('pmg/goal_requests', methods=['GET'])
@login_required
def goal_requests():
    # Hämta alla mål-förfrågningar där du är mottagare och de inte är bekräftade
    received_requests = SharedItem.query.filter_by(user_id=current_user.id, confirmed=False).all()

    # Hämta alla mål-förfrågningar du har skickat men som inte är bekräftade
    sent_requests = SharedItem.query.filter(SharedItem.created_by == current_user.id, SharedItem.confirmed == False).all()

    return render_template('goal_requests.html', received_requests=received_requests, sent_requests=sent_requests)

# endregion

#region Milestones
@pmg_bp.route('milestones/<int:goal_id>')
@login_required
def milestones(goal_id):
    return render_template('pmg/milestones.html')

# endregion

# region Start
@pmg_bp.route('/myday', methods=['GET', 'POST'])
@login_required
def myday():
    sida, sub_menu = common_route("Min Grind", ['/pmg/timebox'], ['My Day'])
    date_now = date.today()
    now = datetime.now()
    today = datetime.now().date()  # Hämta aktuell tid
    tomorrow = today + timedelta(days=1)
    hour = now.hour  # Aktuell timme
    myStreaks = filter_mod(Streak, user_id=current_user.id)
    myScore, total = myDayScore(date_now, current_user.id)
    today_score = get_today_score(current_user.id)
    yesterday_score = get_yesterday_score(current_user.id)
    total, point_details = myDayScore(date_now, current_user.id)
    activity_points = point_details.get("activity_points", 0)
    streak_points = point_details.get("streak_points", 0)

    this_week_scores, last_week_scores = get_weekly_scores(current_user.id)
    plot_url = create_week_comparison_plot(this_week_scores, last_week_scores)

    # Hämta aktiviteter
    myActs = Activity.query.filter_by(user_id=current_user.id)

    aggregated_scores = {
        "activity_points": activity_points,
        "streak_points": streak_points,
        "total_points": total
    }

    valid_streaks=SortStreaks(myStreaks)

    if hour < 14:
        message = "Vad är viktigt för dig att tänka på idag?"
        list_type = "priorities"
        list_date = today
    else:
        message = "Vad kan vara viktigt att tänka på till imorgon?"
        list_type = "priorities"
        list_date = tomorrow

    list_title = "Priorities"
    topFive = TopFive.query.filter_by(title=list_title, user_id=current_user.id, list_type=list_type, date=list_date).first()

    if topFive.content:
        topFiveList = topFive.content.split(',')
        show = 0
    else:
        show = 1
        topFive = TopFive(user_id=current_user.id, list_type=list_type, title=list_title,
                          date=list_date)
        db.session.add(topFive)
        db.session.commit()
        topFiveList = []

    # Hantera POST-begäran för att spara prioriteringar
    if 'my_list' in request.form:
        # Hämta användarens inmatningar
        my_list = [request.form.get(f'Prio_{i}') for i in range(1, 6) if request.form.get(f'Prio_{i}')]
        topFive = TopFive.query.filter_by(title=list_title, user_id=current_user.id, list_type=list_type, date=list_date).first()

        if topFive:
            topFive.content = ','.join(my_list)
        else:
            # Skapa en ny post om den inte finns
            topFive = TopFive(title=list_title, content=','.join(my_list), user_id=current_user.id,
                              list_type=list_type, date=list_date)
            db.session.add(topFive)


        # Spara ändringar i databasen
        try:
            db.session.commit()
            flash("Dina prioriteringar har sparats!", "success")
        except Exception as e:
            db.session.rollback()
            print("Fel vid sparning:", str(e))
            flash("Ett fel inträffade vid sparningen.", "danger")


    return render_template('pmg/myday.html', sida=sida, header=sida, current_date=date_now,
                           acts=myActs, total_score=total, aggregated_scores=aggregated_scores,show=show, my_streaks=valid_streaks,
                           sub_menu=sub_menu, plot_url=plot_url, message=message, topFiveList=topFiveList,topFive=topFive)


@pmg_bp.route('/myday/<date>')
@login_required
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    session = scoped_session(db.session)
    today = datetime.now().date()
    completed_streakNames = completed_streaks(selected_date.strftime('%Y-%m-%d'),Dagar)

    for name in completed_streakNames:
        print(name)

    with session.begin():
        myGoals = filter_mod(Goals, user_id = current_user.id)
        myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != today).all()
        myScore, total = myDayScore(selected_date, current_user.id)

    if selected_date < today:
        sida='Past Day'
        return render_template('cal/pastDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    elif selected_date > today:
        sida = 'Post Day'
        return render_template('cal/postDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    else:
        return redirect(url_for('pmg.myday'))
# endregion

#region Activity

@pmg_bp.route('/update-task-order', methods=['POST'])
@login_required
def update_task_order():
    data = request.get_json()

    # Uppdatera ordningen för varje task och subtask
    for task_data in data:
        task_id = int(task_data['id'])
        task = ToDoList.query.get(task_id)
        if task:
            task.order = task_data['order']
            db.session.add(task)

        for subtask_data in task_data['subtasks']:
            subtask_id = int(subtask_data['id'])
            subtask = SubTask.query.get(subtask_id)
            if subtask:
                subtask.order = subtask_data['order']
                db.session.add(subtask)

    db.session.commit()
    return jsonify({'success': True})

@pmg_bp.route('/focus_room/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def focus_room(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    goal_id = activity.goal_id  # Hämta goal_id från aktiviteten
    today = date.today()
    current_date=today
    tasks = get_user_tasks(current_user.id, Activity,activity_id)  # Hämta och sortera tasks

    activity_notes = Notes.query.filter_by(user_id=current_user.id, activity_id=activity_id).all()
    if request.method == 'POST':
        if 'save-score' in request.form['action']:
            score_str = request.form.get('score', '').strip()
            if score_str:
                try:
                    score_check = float(score_str)
                    if score_check >= 1:
                        add2db(Score, request, ['gID', 'aID', 'aDate', 'start', 'end', 'score'],
                               ['Goal', 'Activity', 'Date', 'Start', 'End', 'Time'], current_user)
                        return redirect(url_for('pmg.myday'))
                except ValueError:
                    print(f"Invalid score value: {score_str}")
            else:
                print("Score field is empty")

    if request.method == 'POST':
        task_id = request.json.get('taskId')
        completed = request.json.get('completed')

        task = ToDoList.query.get_or_404(task_id)
        task.completed = completed
        db.session.commit()

        return jsonify({"success": True}), 200

    return render_template('pmg/focus_room.html',activity_notes=activity_notes, activity=activity, tasks=tasks, current_date=current_date)

@pmg_bp.route('/activity/<int:activity_id>/update_task/<int:task_id>', methods=['GET','POST'])
def update_task(activity_id, task_id):
    task = ToDoList.query.get_or_404(task_id)

    # Hämta den nya statusen från formuläret
    completed = 'completed' in request.form  # Checkbox skickar bara värde om den är markerad
    origin = request.form.get('origin')  # Hämta ursprungssidan

    # Uppdatera task status
    task.completed = completed
    db.session.commit()

    # Omdirigera till rätt sida baserat på ursprungssidan
    if origin == 'todo':
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))
    elif origin == 'focus':
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))

    # Om ingen origin skickas med, omdirigera till standard-sidan
    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

@pmg_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)

    try:
        # Ta bort relaterade tasks
        ToDoList.query.filter_by(activity_id=activity.id).delete()

        # Ta bort relaterade notes
        Notes.query.filter_by(activity_id=activity.id).delete()

        # Ta bort själva aktiviteten
        db.session.delete(activity)
        db.session.commit()

        flash("Aktiviteten har tagits bort.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('pmg.activities'))


@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id)
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]

    return jsonify(activity_list)

@pmg_bp.route('/update_note/<int:note_id>', methods=['POST'])
@login_required
def update_note(note_id):
    note = Notes.query.get_or_404(note_id)

    # Kontrollera om användaren äger anteckningen
    if note.user_id != current_user.id:
        flash('You are not authorized to edit this note.', 'danger')
        return redirect(url_for('pmg.goals'))  # Omdirigera om användaren inte äger anteckningen

    # Uppdatera innehållet från formuläret
    note.content = request.form.get('content')

    db.session.commit()
    flash('Note updated successfully!', 'success')

    return redirect(url_for('pmg.myday'))  # Omdirigera till lämplig sida efter uppdatering

@pmg_bp.route('/create_notebook/<int:activity_id>', methods=['POST'])
@login_required
def create_notebook(activity_id):
    title = request.form.get('title')
    description = request.form.get('description')
    user = User.query.filter_by(id=current_user.id).first()

    new_note = Notes(
        title=title,
        content=description or '',
        user_id=current_user.id,
        author=user.username,
        activity_id=activity_id,
        date=datetime.now().strftime('%Y-%m-%d')
    )
    db.session.add(new_note)
    db.session.commit()

    flash('Notebook created successfully!', 'success')
    return redirect(url_for('pmg.focus_room',activity_id=activity_id))  # Omdirigera till mål-sidan eller var du vill

# endregion

# region Todos
@pmg_bp.route('/activity/<int:activity_id>/tasks', methods=['GET'])
def activity_tasks(activity_id):
    # Hämta aktiviteten
    activity = Activity.query.get_or_404(activity_id)

    # Kontrollera om användaren har åtkomst till aktiviteten
    if activity.goal_id not in [goal.id for goal in get_user_goals(current_user.id)]:
        flash("Du har inte behörighet att visa denna aktivitet.", "danger")
        return redirect(url_for('pmg.myday'))  # Omdirigera till en lämplig sida

    # Hämta tasks och subtasks kopplade till aktiviteten
    todos = get_user_tasks(current_user.id, Activity, activity_id)  # Använd den uppdaterade funktionen

    sida = f"{activity.name} ToDos"
    return render_template('pmg/activity_tasks.html', activity=activity, tasks=todos, sida=sida, header=sida)


@pmg_bp.route('/activity/<int:activity_id>/add_task', methods=['POST'])
def add_task(activity_id):
    # Hämta aktiviteten
    activity = Activity.query.get_or_404(activity_id)

    # Kontrollera om aktiviteten är kopplad till ett SharedItem
    shared_item = SharedItem.query.filter_by(
        id=activity.shared_item_id
    ).first()

    # Hämta data från formuläret
    task_name = request.form.get('task_name')
    is_repeatable = request.form.get('is_repeatable') == 'true'
    total_repeats = request.form.get('total_repeats', type=int)

    # Validera task-namn
    if not task_name:
        flash("Task name is required", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    # Skapa ny task
    new_task = ToDoList(
        task=task_name,
        completed=False,
        is_repeatable=is_repeatable,
        total_repeats=total_repeats if is_repeatable else None,
        user_id=current_user.id,
        activity_id=activity.id,
        shared_item_id=shared_item.id if shared_item else None
    )

    db.session.add(new_task)
    db.session.commit()

    if shared_item:
        # Hämta alla användare som delar aktiviteten
        shared_users = SharedItem.query.filter_by(item_id=activity.id, item_type='activity', status='active').all()
        for shared_user in shared_users:
            if shared_user.shared_with_id != current_user.id:
                create_notification(
                    user_id=shared_user.shared_with_id,
                    message=f"{current_user.username} added the task '{task_name}' to '{activity.name}'.",
                    related_item_id=new_task.id,
                    item_type='task'
                )

    flash("Task added successfully", "success")
    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

@pmg_bp.route('/activity/<int:activity_id>/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(activity_id, task_id):
    # Hämta tasken
    task = ToDoList.query.get_or_404(task_id)

    # Kontrollera om användaren har åtkomst till aktiviteten
    if task.activity_id != activity_id:
        flash("Ogiltig förfrågan: Aktiviteten matchar inte.", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    # Kontrollera om användaren är ägare till tasken eller att aktiviteten är delad
    if not current_user.id == task.user_id:
        flash("Du har inte behörighet att ta bort denna task.", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task raderades framgångsrikt.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))


# endregion

#region Subtasks
@pmg_bp.route('/task/<int:task_id>/add_subtask', methods=['POST'])
@login_required
def add_subtask(task_id):
    task = ToDoList.query.get_or_404(task_id)
    subtask_name = request.form.get('subtask_name')

    if not subtask_name:
        flash("Subtask name is required", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))

    new_subtask = SubTask(name=subtask_name, task_id=task_id)
    db.session.add(new_subtask)
    db.session.commit()

    flash("Subtask added successfully!", "success")
    return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))

@pmg_bp.route('/subtask/<int:subtask_id>/update', methods=['POST'])
@login_required
def update_subtask(subtask_id):
    subtask = SubTask.query.get_or_404(subtask_id)
    subtask.completed = not subtask.completed
    db.session.commit()
    flash("Subtask updated successfully!", "success")
    return redirect(url_for('pmg.get_subtasks', task_id=subtask.task_id))


@pmg_bp.route('/task/<int:task_id>/subtasks', methods=['GET'])
@login_required
def get_subtasks(task_id):
    task = ToDoList.query.get_or_404(task_id)
    subtasks = SubTask.query.filter_by(task_id=task_id).all()
    return render_template('pmg/subtasks.html', task=task, subtasks=subtasks)

#endregion


