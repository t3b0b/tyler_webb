from models import (User, db, Streak, BloggPost, Goals, Friendship, Bullet, Task,
                    Activity, Score, MyWords, Settings, Dagar, Message,ToDoList,
                    Idag, Week, Month, WhyGoals,Event,CalendarBullet,ViewType)
from datetime import datetime, timedelta, date
import pandas as pd
from pytz import timezone
from flask_login import current_user


# region Functions
def section_content(db,section):
    list = db.query.filter_by(name=section).first()
    return list

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


def getWord():
    ord_lista = MyWords.query.filter_by(user_id=current_user.id).all()
    ordet = None
    for ord in ord_lista:
        if not ord.used:
            # Uppdatera ordet till att vara använt
            ord.used = True
            db.session.commit()

            ordet = ord.word
            break
    return ordet, ord_lista


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


def process_weekly_scores(scores, start_week, end_week):
    week_days = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']
    weekly_data = {day: {} for day in week_days}

    for score in scores:
        score_date = datetime.strftime(score.Date, '%Y-%m-%d')  # Använd datumet direkt som date objekt
        parsed_date = parse_date(score_date)
        day_of_week = (parsed_date - start_week).days
        day_name = week_days[day_of_week]

        if isinstance(score.Time, str):
            hour = int(score.Time.split(':')[0])  # Konvertera tiden till timme som ett heltal om den är en sträng
        elif isinstance(score.Time, int):
            hour = score.Time  # Om tiden redan är en int, använd den direkt
        else:
            continue  # Om tiden är i ett oväntat format, hoppa över denna post

        if hour not in weekly_data[day_name]:
            weekly_data[day_name][hour] = []

        weekly_data[day_name][hour].append(score.activity_name)

    return weekly_data


def readWords(filename):
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-8-sig']
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as file:
                data = file.read()
                ordet = data.split('\n')[0]
                ord_lista = data.split('\n')[1:]
                return ordet, ord_lista
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Could not decode the file {filename} with any of the tried encodings.")


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


def add2db(db_model, request, form_fields, model_fields, user):
    new_entry = db_model()
    current_date = datetime.now()  # Använd YYYY-MM-DD format

    # Iterera över form_fields och model_fields och sätt attribut på new_entry
    for form_field, model_field in zip(form_fields, model_fields):
        value = request.form[form_field]
        if model_field in ['Start', 'End']:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
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

    # Lägg till den nya posten i sessionen och committa
    db.session.add(new_entry)
    db.session.commit()


def query(db, key, filter):
    return db.query.filter_by(**{key: filter}).all()


def unique(db, by_db):
    unique_data = [post.title for post in db.query.with_entities(by_db).distinct().all()]
    list = [item[0] for item in unique_data]
    return list


def update_dagar(user_id, model):
    today = date.today()
    my_Score, total = myDayScore(today, user_id)
    my_streaks = Streak.query.filter_by(user_id=user_id).all()
    tot_streaks = len(my_streaks)

    if my_streaks:
        active_streaks = Streak.query.filter_by(user_id=user_id, active=True).all()
        completed = len(active_streaks)
        streakNames = ""

        for i, streak in enumerate(active_streaks):
            if i == completed:
                streakNames += streak.name
            elif i < completed:
                streakNames += streak.name + ','
        dag = model.query.filter_by(date=today, user_id=user_id).first()
        if dag is None:
            dag = model(user_id=user_id, date=today, total_streaks=tot_streaks, completed_streaks=completed,
                        completed_streaks_names=streakNames, total_points=total)
            db.session.add(dag)
            db.session.commit()
        else:
            dag.completed_streaks = completed
            dag.total_streaks = tot_streaks
            dag.completed_streaks_names = streakNames
            dag.total_points = total
            db.session.commit()


def completed_streaks(day, model=Dagar):
    dag = model.query.filter_by(user_id=current_user.id, date=day).first()
    if dag and dag.completed_streaks_names:
        names_list = dag.completed_streaks_names.split(',')
        return [name.strip() for name in names_list]
    return []


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
        # Uppdatera level baserat på count
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


def myDayScore(date, user_id):
    total = 0
    myScore = db.session.query(
        Goals.name.label('goal_name'),
        Activity.name.label('activity_name'),
        Score.Date,
        Score.Time,
        Streak.name.label('streak_name')
    ).outerjoin(
        Goals, Goals.id == Score.Goal
    ).outerjoin(
        Activity, Activity.id == Score.Activity
    ).outerjoin(
        Streak, Streak.id == Score.Streak
    ).filter(
        Score.Date == date
    ).filter(
        Score.user_id == user_id
    ).all()

    for score in myScore:
        total += float(score.Time)
        total = int(total)
    return myScore, total


def generate_calendar_weeks(year, month):
    first_day_of_month = datetime(year, month, 1)
    days = []
    string_day = []
    # Föregående månad
    previous_month_day = first_day_of_month - timedelta(days=1)

    while previous_month_day.weekday() != 6:  # Söndag är 6 i weekday() funktionen
        days.insert(0, {'day': previous_month_day.day, 'date': previous_month_day, 'current_month': False})
        previous_month_day -= timedelta(days=1)

    # Aktuell månad
    current_day = first_day_of_month
    while current_day.month == month:
        days.append({'day': current_day.day, 'date': current_day, 'current_month': True})
        current_day += timedelta(days=1)

    # Nästkommande månad
    while len(days) % 7 != 0:
        days.append({'day': current_day.day, 'date': current_day, 'current_month': False})

        current_day += timedelta(days=1)
        string_day.append(current_day)
    # Dela upp dagarna i veckor
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    return weeks


def getInfo(filename, page):
    df = pd.read_csv(filename)
    row = df.loc[df['Page'] == page]
    if not row.empty:
        return row.iloc[0]['Info']
    else:
        return "Ingen information tillgänglig för den angivna sidan."

# endregion