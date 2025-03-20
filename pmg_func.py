from models import (Streak, Goals, Friendship, 
                    Activity, Score,ToDoList,SharedItem,
                    Notification)
from extensions import db

from datetime import datetime, timedelta, date
import pandas as pd
from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from calendar import monthrange

# region Functions

STOCKHOLM_TZ = timezone('Europe/Stockholm')

def read_info(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

def organize_activities_by_time(activities):
    activities_dict = {}
    for score, activity_name, goal_name in activities:
        day = score.Start.strftime('%A')
        hour = score.Start.hour
        print(hour)
        if day not in activities_dict:
            activities_dict[day] = {}
        if hour not in activities_dict[day]:
            activities_dict[day][hour] = []
        activities_dict[day][hour].append({
            'activity_name': activity_name,
            'goal_name': goal_name
        })
    return activities_dict

def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')

def common_route(title, sub_url, sub_text):
    sida = title
    sub_menu = []
    if sub_text:
        for i, url in enumerate(sub_url):
            sub_menu.append({
                'choice': url,
                'text': sub_text[i]
            })
        return sida, sub_menu
    else:
        return sida, None

# endregion

# region Goals
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

# endregion

# region Activities
def get_activities_for_goal(user_id, goal_id):
    # Kontrollera om målet finns bland användarens tillåtna mål
    all_goals = get_user_goals(user_id)
    allowed_goal_ids = [goal.id for goal in all_goals]

    if goal_id not in allowed_goal_ids:
        raise ValueError("Användaren har inte tillgång till detta mål.")

    # Hämta aktiviteter kopplade till det specifika målet
    return Activity.query.filter_by(goal_id=goal_id).all()

def get_activities_for_user(user_id, start_date, end_date):
    tz = timezone('Europe/Stockholm')  # Byt till din aktuella tidszon om den skiljer sig
    start_date = start_date.astimezone(tz)
    end_date = end_date.astimezone(tz)
    return db.session.query(
        Score,
        Activity.name.label('activity_name'),
        Goals.name.label('goal_name')
    ).join(
        Activity, Activity.id == Score.Activity
    ).outerjoin(
        Goals, Goals.id == Score.Goal
    ).filter(
        Score.user_id == user_id,
        Score.Start >= start_date,
        Score.End <= end_date
    ).all()

# endregion

# region Friends
def delete_old_notifications():
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    Notification.query.filter(Notification.created_at < cutoff_date).delete()
    db.session.commit()

def create_notification(user_id, message, related_item_id=None, item_type=None):
    """
    Skapa och spara en notifikation i databasen.

    :param user_id: ID för användaren som notifikationen är riktad till
    :param message: Notifikationsmeddelandet
    :param related_item_id: ID för det relaterade objektet (t.ex. mål eller aktivitet)
    :param item_type: Typ av objekt (t.ex. 'goal', 'activity', 'task')
    """
    notification = Notification(
        user_id=user_id,
        message=message,
        related_item_id=related_item_id,
        item_type=item_type
    )
    db.session.add(notification)
    db.session.commit()

# endregion

# region db

def filter_mod(model, **filters):

    query = model.query
    filter_conditions = []

    try:
        for field, value in filters.items():
            filter_conditions.append(getattr(model, field) == value)

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        return query.all()

    except SQLAlchemyError as e:
        # Logga felet och gör rollback
        db.session.rollback()  # Rollback till senaste fungerande state
        print(f"Error during query execution: {str(e)}")
        return None

def add2db(db_model, request, form_fields, model_fields, user):
    new_entry = db_model()
    current_date = datetime.now()  # Använd YYYY-MM-DD format

    # Iterera över form_fields och model_fields och sätt attribut på new_entry
    for form_field, model_field in zip(form_fields, model_fields):
        value = request.form.get(form_field)  # Använd .get() för att undvika KeyError
        if model_field in ['Start', 'End'] and value:  # Endast om värdet finns
            try:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                # Hantera fel, t.ex. logga fel eller flasha ett felmeddelande
                print(f"Fel vid konvertering av tid: {e}")
                value = None  # Eller hantera på ett annat sätt
        setattr(new_entry, model_field, value)

    # Lägg till user_id om det är en del av modellen
    if hasattr(new_entry, 'user_id'):
        setattr(new_entry, 'user_id', user.id)
    if hasattr(new_entry, 'date'):
        setattr(new_entry, 'date', current_date)
    if hasattr(new_entry, 'author'):
        setattr(new_entry, 'author', user.username)
    if hasattr(new_entry, 'active'):
        setattr(new_entry, 'active', False)

    # Kontrollera och sätt lastReg och dayOne
    if hasattr(new_entry, 'lastReg'):
        setattr(new_entry, 'lastReg', current_date)
    if hasattr(new_entry, 'level'):
        setattr(new_entry, 'level', 1)
    if hasattr(new_entry, 'dayOne'):
        setattr(new_entry, 'dayOne', current_date)

    if hasattr(new_entry, 'goal_id') and 'goalSelect' in request.form:
        goal_id_value = request.form.get('goalSelect')
        setattr(new_entry, 'goal_id', goal_id_value if goal_id_value else None)
        if goal_id_value:  # Kontrollera om värdet inte är tomt
            setattr(new_entry, 'goal_id', goal_id_value)
        else:
            setattr(new_entry, 'goal_id', None)
    try:
    # Lägg till den nya posten i sessionen och committa
        db.session.add(new_entry)
        db.session.commit()
    except:
        db.session.rollback()  # Lägg till detta för att säkerställa rollback på fel

# endregion

# region Streak

def get_yesterdays_streak_values(user_id):
    yesterday = datetime.now().date() - timedelta(days=1)  # Gårdagens datum

    results = db.session.query(
        Streak.id,
        Streak.name,
        Streak.amount,
        Score.Amount.label('yesterday_value')
    ).join(Score, and_(
        Score.Streak == Streak.id,  # Koppla score till streak
        Score.Date == yesterday,  # Endast gårdagens datum
        Score.user_id == user_id  # Endast för aktuell användare
    )).filter(
        Streak.user_id == user_id,  # Endast aktuella användarens streaks
        Streak.type == 'number'  # Endast streaks som har type="number"
    ).all()

    return results 

def SortStreaks(Streaks):
    valid_streaks = []
    now = getSwetime()

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

def update_streak_details(streak, today):
    if today != streak.lastReg:
        count = streak.count
        if count == 0:
            streak.dayOne = today
        best_now = streak.best
        count += streak.interval
        streak.active = True
        streak.count = count
        streak.lastReg = today

        if best_now < count:
            best_now = count
            streak.best = best_now

        if streak.goal_id:
            goal_id = streak.goal_id
        else:
            goal_id = None
        if 0 <= count <= 10:
            streak.level = 1
            score = 10
        elif 11 <= count <= 20:
            streak.level = 2
            score = 12
        elif 21 <= count <= 30:
            streak.level = 3
            score = 13
        elif 31 <= count <= 50:
            streak.level = 4
            score = 14
        elif 51 <= count <= 70:
            streak.level = 5
            score = 15
        elif 71 <= count <= 90:
            streak.level = 6
            score = 16
        elif 91 <= count <= 110:
            streak.level = 7
            score = 17
        elif 111 <= count <= 130:
            streak.level = 8
            score = 18
        elif 131 <= count <= 150:
            streak.level = 9
            score = 19
        elif count >= 151:
            streak.level = 10
            score = 20

        db.session.commit()

        return score, goal_id

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

# endregion

# region Get

def get_user_tasks(user_id, model, activity_id=None):
    # Hämta alla aktiviteter som användaren har tillgång till
    all_activities = model.query.filter_by(user_id=user_id).all()
    activity_ids = [activity.id for activity in all_activities]

    # Om activity_id anges, filtrera på den specifika aktiviteten
    query = ToDoList.query.filter(ToDoList.activity_id.in_(activity_ids))
    if activity_id:
        query = query.filter(ToDoList.activity_id == activity_id)

    # Ladda subtasks och sortera tasks
    tasks = query.options(db.joinedload(ToDoList.subtasks)).order_by(
        ToDoList.completed.desc(), ToDoList.task.asc()
    ).all()

    # Lägg till antalet avklarade och oavklarade deluppgifter
    for task in tasks:
        task.subtask_count = len(task.subtasks)  # Totalt antal deluppgifter
        task.completed_subtasks = sum(1 for subtask in task.subtasks if subtask.completed)
        task.pending_subtasks = task.subtask_count - task.completed_subtasks  # Oavklarade deluppgifter

    return tasks
def getInfo(filename, page):
    df = pd.read_csv(filename)
    row = df.loc[df['Page'] == page]
    if not row.empty:
        return row.iloc[0]['Info']
    else:
        return "Ingen information tillgänglig för den angivna sidan."

def getSwetime():
    now = datetime.now(STOCKHOLM_TZ)
    return now

# endregion