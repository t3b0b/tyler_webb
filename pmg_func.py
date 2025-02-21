from models import (User, db, Streak, Notes, Goals, Friendship, Bullet,
                    Activity, Score, MyWords, Settings, Dagar, Message, ToDoList,
                    Event, TopFive,Notification)
from random import choice
import random
from datetime import datetime, timedelta, date
import pandas as pd
from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

# region Functions

STOCKHOLM_TZ = timezone('Europe/Stockholm')

def read_info(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()
    

def get_daily_question():

    Questions = {
    "Prioriteringar": ["Viktigt att prioritera idag",
                   'Viktigt att prioritera imorgon'],
    "Tacksam": ["Vad har du att vara tacksam för?"],
    "Tankar": ["Tankar/insikter värda att påminnas om",
               "Tankar/insikter att ta med till imorgon"],
    "Bättre": ["Vad ska du se till att göra bättre idag?",
               "Vad ska du se till att göra bättre imorgon?"],
    "Känslor": ["Hur känner du dig idag?",
                "Hur känner du inför imorgon?"],
    "Mål": ["Vilka mål vill du nå idag?",
            "Vilka mål vill du nå imorgon?"],
    "Relationer": ["Finns det någon du vill ge extra uppmärksamhet till idag?",
                   "Finns det någon du vill ge extra uppmärksamhet till imorgon?"],
    "Lärande": ["Vad vill du lära dig eller utforska idag?",
                "Vad vill du lära dig eller utforska imorgon?"],
    "Hälsa": ["Vad kan du göra idag för att ta hand om din hälsa och energi?",
              "Vad kan du göra imorgon för att ta hand om din hälsa och energi?"],
    "Uppskattning": ["Vad eller vem kan du visa uppskattning för idag?",
                     "Vad eller vem kan du visa uppskattning för imorgon?"],
    "Kreativitet": ["Hur kan du uttrycka din kreativitet idag?",
                    "Hur kan du uttrycka din kreativitet imorgon?"],
    "Utmaningar": ["Finns det någon utmaning du kan ta itu med idag?",
                   "Finns det någon utmaning du kan ta itu med imorgon?"],
    "Avslappning": ["Vad kan du göra för att slappna av och återhämta dig idag?",
                    "Vad kan du göra för att slappna av och återhämta dig imorgon?"],
    "Underlätta": ["Vad kan du göra idag för att underlätta morgondagen?",
                    "Vad kan du göra för att underlätta den här dagen?"],
}
    
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    hour = datetime.now().hour
    
    random.seed(str(today))  # Samma fråga varje dag
    list_type = random.choice(list(Questions.keys()))  # Välj en slumpmässig kategori

    if hour < 14:
        message = Questions[list_type][0]  # Första frågan
        list_date = today
    else:
        message = Questions[list_type][1] if len(Questions[list_type]) > 1 else Questions[list_type][0]
        list_date = tomorrow  # Sätter frågan till morgondagens datum om klockan är efter 14:00

    return message, list_type, list_date

def getSwetime():
    now = datetime.now(STOCKHOLM_TZ)
    return now

def delete_old_notifications():
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    Notification.query.filter(Notification.created_at < cutoff_date).delete()
    db.session.commit()

def add_words_from_file(file_name, user_id):
    try:
        _, word_list = readWords(file_name)
        added_count = 0
        for word in word_list:
            try:
                add_unique_word(word, user_id)
                added_count += 1
            except Exception as e:
                print(f"Could not add word '{word}': {e}")
        return f"{added_count} words added successfully."
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def add_unique_word(word, user_id):
    # Kontrollera om ordet redan finns
    existing_word = MyWords.query.filter_by(word=word).first()
    if existing_word:
        return f"Word '{word}' already exists!", False  # Returnera ett felmeddelande

    # Skapa nytt ord
    new_word = MyWords(word=word, user_id=user_id)
    db.session.add(new_word)
    db.session.commit()
    return f"Word '{word}' added successfully!", True

def section_content(db,section):
    list = db.query.filter_by(name=section).first()
    return list

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

def unique(db, by_db):
    unique_data = [post.title for post in db.query.with_entities(by_db).distinct().all()]
    list = [item[0] for item in unique_data]
    return list

def update_dagar(user_id, model):
    today = date.today()
    total_points, point_details = myDayScore(today, user_id)
    activity_points = point_details.get("activity_points", 0)
    streak_points = point_details.get("streak_points", 0)

    my_streaks = Streak.query.filter_by(user_id=user_id).all()
    tot_streaks = len(my_streaks)

    if my_streaks:
        active_streaks = Streak.query.filter_by(user_id=user_id, active=True).all()
        completed = len(active_streaks)
        streakNames = ", ".join(streak.name for streak in active_streaks)

        dag = model.query.filter_by(date=today, user_id=user_id).first()
        if dag is None:
            dag = model(
                user_id=user_id,
                date=today,
                total_streaks=tot_streaks,
                completed_streaks=completed,
                completed_streaks_names=streakNames,
                total_points=total_points,
            )
            db.session.add(dag)
        else:
            dag.completed_streaks = completed
            dag.total_streaks = tot_streaks
            dag.completed_streaks_names = streakNames
            dag.total_points = total_points
            dag.streak_points = streak_points
            dag.activity_points = activity_points
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
    # Beräkna streaks-poäng
    streak_points = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == date,
        Score.Activity == None  # Streaks har ingen aktivitet kopplad
    ).scalar() or 0

    # Beräkna aktivitetspoäng
    activity_points = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == date,
        Score.Activity != None  # Poäng kopplade till aktiviteter
    ).scalar() or 0

    # Totalpoäng
    total_points = streak_points + activity_points

    # Returnera totalpoäng och en ordbok med detaljer
    return total_points, {
        "streak_points": streak_points,
        "activity_points": activity_points
    }

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

def send_streak_notifications(streak_id, message, request_help=False):
    """Notifierar användare om en streak, kan även be om hjälp att rädda den."""
    shared_items = SharedItem.query.filter_by(item_type='streak', item_id=streak_id, status='active').all()

    for shared_item in shared_items:
        if shared_item.shared_with_id != current_user.id:
            if request_help:
                message = f"{current_user.username} behöver hjälp med streak: {shared_item.streak.name}."
            create_notification(
                user_id=shared_item.shared_with_id,
                message=message,
                related_item_id=streak_id,
                item_type='streak'
            )

def get_weekly_scores(user_id):
    today = datetime.now()  # Byt från utcnow() till now()
    start_of_this_week = today - timedelta(days=today.weekday())  # Får måndag denna vecka (kl 00:00)
    start_of_last_week = start_of_this_week - timedelta(days=7)  # Måndag förra veckan
    end_of_last_week = start_of_this_week - timedelta(days=1)  # Söndag förra veckan

    # Hämta poäng från databasen
    this_week_scores = db.session.query(
        Score.Date, db.func.sum(Score.Time).label('total_points')
    ).filter(
        Score.user_id == user_id,
        Score.Date >= start_of_this_week.date(),  # Fixar måndagsproblemet
        Score.Date <= today.date()  # Endast till idag, ej framtida poster
    ).group_by(Score.Date).all()

    last_week_scores = db.session.query(
        Score.Date, db.func.sum(Score.Time).label('total_points')
    ).filter(
        Score.user_id == user_id,
        Score.Date >= start_of_last_week.date(),  # Använder .date() för att jämföra rätt
        Score.Date <= end_of_last_week.date()
    ).group_by(Score.Date).all()

    activity_times = db.session.query(
        Activity.name,
        db.func.sum(Score.Time).label('total_time')
    ).join(Score).filter(
        Score.user_id == user_id,
        Score.Date.between(start_of_this_week.date(), today.date())
    ).group_by(Activity.name).all()

    return this_week_scores, last_week_scores, activity_times

def create_week_comparison_plot(this_week_scores, last_week_scores):

    days = ['Mån', 'Tis', 'Ons', 'Tors', 'Fre', 'Lör', 'Sön']
    x = range(len(days))

    # Konvertera datan till en form som passar grafer
    this_week_data = {score.Date.weekday(): score.total_points for score in this_week_scores}
    last_week_data = {score.Date.weekday(): score.total_points for score in last_week_scores}

    this_week = [this_week_data.get(i, 0) for i in range(7)]
    last_week = [last_week_data.get(i, 0) for i in range(7)]

    plt.figure(figsize=(10, 6))
    plt.bar(x, last_week, alpha=0.5, label="Föregående vecka", color="blue")
    plt.bar(x, this_week, alpha=1, label="Aktuell vecka", color="orange")
    plt.xticks(x, days)
    plt.ylabel("Totala poäng")
    plt.xlabel("Veckodag")
    plt.legend()
    plt.tight_layout()

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


def get_user_tasks(user_id, model, activity_id=None):
    # Hämta alla aktiviteter som användaren har tillgång till
    all_activities = model.query.filter_by(user_id=user_id).all()

    activity_ids = [activity.id for activity in all_activities]

    # Om activity_id anges, filtrera på den specifika aktiviteten
    query = ToDoList.query.filter(ToDoList.activity_id.in_(activity_ids))
    if activity_id:
        query = query.filter(ToDoList.activity_id == activity_id)

    # Sortera tasks (avklarade först, sedan alfabetiskt)
    return query.options(db.joinedload(ToDoList.subtasks)).order_by(ToDoList.completed.desc(),
                                                                    ToDoList.task.asc()).all()


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


def get_score_for_day(user_id, day_offset=0):
    """Hämta score för en viss dag. day_offset=0 för idag, day_offset=1 för igår osv."""
    target_date = datetime.now().date() - timedelta(days=day_offset)
    return db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == target_date
    ).scalar() or 0


def create_activity_plot(activity_times):
    """Generera en stående stapelgraf med unika färger för varje mål."""
    activity_names = [activity[0] for activity in activity_times]
    total_times = [activity[1] for activity in activity_times]

    # Färger för varje stapel, genereras automatiskt för att vara unika
    colors = plt.cm.get_cmap('tab20', len(activity_names))(range(len(activity_names)))
    plt.figure(figsize=(10, 8), facecolor='none', edgecolor='k', )
    plt.bar(activity_names, total_times, color=colors)  # Stående staplar
    plt.ylabel('Total Tid (min)', fontsize=10)
    plt.xlabel('Aktivitet', fontsize=10)
    plt.xticks(rotation=0, ha='center', fontsize=14)
    plt.yticks(rotation=0, ha='right', fontsize=14)
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

# endregion