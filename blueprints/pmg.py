from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, db, Streak, BloggPost, Goals, Friendship, Bullet, ToDoList,
                    Activity, Score, MyWords, Settings, Dagbok, Dagar, Message,
                    Idag, Week, Month, WhyGoals)
from datetime import datetime, timedelta, date
import pandas as pd
from pytz import timezone
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

pmg_bp = Blueprint('pmg', __name__, template_folder='templates/pmg')

#region Functions
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
    return ordet,ord_lista
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
        score_date = datetime.strftime(score.Date,'%Y-%m-%d')  # Använd datumet direkt som date objekt
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
def common_route(title,sub_url,sub_text):
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

        if goal_id_value:  # Kontrollera om värdet inte är tomt
            setattr(new_entry, 'goal_id', goal_id_value)
        else:
            setattr(new_entry, 'goal_id', None)

    # Lägg till den nya posten i sessionen och committa
    db.session.add(new_entry)
    db.session.commit()
def query(db, key, filter):
    return db.query.filter_by(**{key: filter}).all()
def unique(db,by_db):
    unique_data = [post.title for post in db.query.with_entities(by_db).distinct().all()]
    list = [item[0] for item in unique_data]
    return list
def section_content(db,section):
    list = db.query.filter_by(name=section).first()
    return list.id
def update_dagar(user_id, model):
    today = date.today()
    my_Score, total = myDayScore(today, user_id)
    my_streaks = Streak.query.filter_by(user_id=user_id).all()
    tot_streaks = len(my_streaks)

    if my_streaks:
        active_streaks = Streak.query.filter_by(user_id=user_id,active=True).all()
        completed = len(active_streaks)
        streakNames = ""

        for i, streak in enumerate(active_streaks):
            if i == completed:
                streakNames += streak.name
            elif i < completed:
                streakNames += streak.name + ','
        dag = model.query.filter_by(date=today,user_id=user_id).first()
        if dag is None:
            dag = model(user_id=user_id, date=today, total_streaks=tot_streaks, completed_streaks=completed, completed_streaks_names=streakNames,total_points=total)
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
            score=14
        elif 51 <= count <= 70:
            streak.level = 5
            score=15
        elif 71 <= count <= 90:
            streak.level = 6
            score=16
        elif 91 <= count <= 110:
            streak.level = 7
            score=17
        elif 111 <= count <= 130:
            streak.level = 8
            score=18
        elif 131 <= count <= 150:
            streak.level = 9
            score=19
        elif count >= 151:
            streak.level = 10
            score=20

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
    string_day=[]
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

@pmg_bp.route('/timer')
def timer():
    sida='Timer'
    duration = request.args.get('duration', default=60, type=int)
    return render_template('pmg/timer.html',sida=sida,
                           header=sida, duration=duration)

#region Streak
@pmg_bp.route('/streak',methods=['GET', 'POST'])
def streak():
    current_date = date.today()
    current_date = current_date.strftime('%Y-%m-%d')
    sida, sub_menu = common_route("Mina Streaks", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks','Goals','Milestones'])
    myStreaks = query(Streak,'user_id',current_user.id)
    myGoals = query(Goals, 'user_id', current_user.id)

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

@pmg_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = date.today()
    current_date = today.strftime('%Y-%m-%d')

    if action == 'check':
        score, goal_id = update_streak_details(streak, today)
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

# region Goals
@pmg_bp.route('/goal/<int:goal_id>/todo', methods=['GET'])
@login_required
def get_todo_list(goal_id):
    # Kontrollera att målet existerar och tillhör den inloggade användaren
    goal = Goals.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Hämta alla uppgifter (tasks) för det specifika målet
    tasks = ToDoList.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()

    # Returnera HTML med att-göra-listan
    return render_template('pmg/todo_list.html', tasks=tasks)

@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    # Ensures that only activities for the current user and specific goal are fetched
    activities = Activity.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]
    return jsonify(activity_list)

@pmg_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    activity = Activity.query.get(activity_id)
    if activity:
        db.session.delete(activity)
        db.session.commit()
        return jsonify(success=True), 200
    return jsonify(success=False), 404

@pmg_bp.route('/goals',methods=['GET', 'POST'])
def goals():
    sida, sub_menu = common_route("Mina Mål", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks','Goals','Milestones'])
    myGoals = query(Goals,'user_id',current_user.id)
    friends = current_user.friends
    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            add2db(Goals, request, ['goalName'], ['name'], current_user)
            return redirect(url_for('pmg.goals', sida=sida, header=sida, goals=myGoals))

        elif 'addActivity' in request.form['action']:
            add2db(Activity, request, ['goalId','activity-name','activity-measurement'],
                   ['goal_id','name','measurement'], current_user)
            return redirect(url_for('pmg.goals',sida=sida,header=sida, goals=myGoals))

        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = ToDoList(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            return redirect(url_for('pmg.goals', sida=sida, header=sida, goals=myGoals))
    return render_template('pmg/goals.html',friends=friends,sida=sida,header=sida, goals=myGoals,sub_menu=sub_menu)

@pmg_bp.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    # Data från JSON-kroppen, om du behöver den
    data = request.get_json()
 # Debug: se vad som faktiskt tas emot

    goal = Goals.query.get(goal_id)
    if goal:
        db.session.delete(goal)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False)
# endregion

#region Milestones
@pmg_bp.route('milestones/<int:goal_id>')
def milestones(goal_id):
    return render_template('pmg/milestones.html')

# endregion

#region MyDay
@pmg_bp.route('/myday', methods=['GET', 'POST'])
@login_required
def myday():
    pageInfo = getInfo('pageInfo.csv', 'Start')
    sida, sub_menu = common_route("Min Grind", ['/pmg/timebox', '/pmg/streak', '/pmg/goals'],
                                  ['My Day', 'Streaks', 'Goals'])
    date_now = date.today()
    update_dagar(current_user.id, Dagar)

    # Använd konsekvent my_goals istället för både my_goals och myGoals
    my_goals = Goals.query.filter_by(user_id=current_user.id).all()
    myStreaks = Streak.query.filter_by(user_id=current_user.id).all()
    myScore, total = myDayScore(date_now, current_user.id)

    aggregated_scores = {}
    current_goal = None

    if request.method == 'POST':
        goal_id = request.form.get('goal_id')
        if goal_id:
            current_goal = Goals.query.get(goal_id)

    # Bygg den aggregerade poänglistan och koppla till to-dos
    for score in myScore:
        activity_name = score.goal_name if score.goal_name else "?"
        if activity_name in aggregated_scores:
            aggregated_scores[activity_name]['total_time'] += float(score.Time)
        else:
            aggregated_scores[activity_name] = {
                'Goal': score.goal_name,
                'Activity': score.activity_name,
                'Streak': score.streak_name,
                'total_time': float(score.Time),
                'todos': []  # Lägg till todos (om det behövs)
            }

    today = datetime.now()
    valid_streaks = []

    for streak in myStreaks:
        interval_days = timedelta(days=streak.interval, hours=23, minutes=59, seconds=59)
        if streak.lastReg:
            try:
                last_reg_date = streak.lastReg
                streak_interval = last_reg_date + interval_days
                if streak.count == 0:
                    valid_streaks.append(streak)
                elif streak.count >= 1:
                    if today.date() == streak_interval.date():
                        valid_streaks.append(streak)
                    elif streak_interval.date() < today.date():
                        continue
                elif streak_interval.date() < today.date():
                    streak.active = False
                    streak.count = 0
                    db.session.commit()
            except (ValueError, TypeError) as e:
                print(f'Hantera ogiltigt datum: {e}, streak ID: {streak.id}, lastReg: {streak.lastReg}')
        else:
            valid_streaks.append(streak)

    if myScore:
        sorted_myScore = sorted(myScore, key=lambda score: score[0])

    if request.method == 'POST':
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

    return render_template('pmg/myday.html', sida=sida, header=sida, current_date=date_now,
                           my_goals=my_goals, my_streaks=valid_streaks, my_score=myScore, total_score=total,
                           sub_menu=sub_menu, sum_scores=aggregated_scores, page_info=pageInfo,
                           current_goal=current_goal)

@pmg_bp.route('/myday/<date>')
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()

    today = datetime.now().date()
    completed_streakNames = completed_streaks(selected_date.strftime('%Y-%m-%d'),Dagar)
    for name in completed_streakNames:
        print(name)
    myGoals = query(Goals, 'user_id', current_user.id)
    myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != today).all()
    myScore = query(Score, 'user_id', current_user.id)
    myScore, total = myDayScore(selected_date, current_user.id)

    if selected_date < today:
        sida='Past Day'
        return render_template('pmg/pastDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    elif selected_date > today:
        sida = 'Post Day'
        return render_template('pmg/postDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    else:
        return redirect(url_for('pmg.myday'))

# endregion

#region Kalender
@pmg_bp.route('/month')
@pmg_bp.route('/month/<int:year>/<int:month>')
def month(year=None, month=None):
    page_info=getInfo('pageInfo.csv', 'myMonth')
    sida, sub_menu = common_route('Min Månad', ['/pmg/month', '/pmg/week', '/pmg/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])

    update_dagar(current_user.id, Dagar)  # Uppdatera Dagar-modellen

    if not year or not month:
        year = datetime.now().year
        month = datetime.now().month

    first_day_of_month = datetime(year, month, 1)
    month_name = first_day_of_month.strftime('%B')

    weeks = generate_calendar_weeks(year, month)

    sida = "Min Kalender"
    today = datetime.now()
    today_date = datetime(today.year, today.month, today.day, 0, 0, 0)

    dag_entries = Dagar.query.filter(Dagar.date >= weeks[0][0]['date'], Dagar.date <= weeks[-1][-1]['date'], Dagar.user_id == current_user.id).all()
    dag_data = {entry.date.strftime('%Y-%m-%d'): entry for entry in dag_entries}

    return render_template('pmg/month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida,
                           sub_menu=sub_menu, month=month, today_date=today_date, dag_data=dag_data,page_info=page_info)

@pmg_bp.route('/week')
def week():
    page_info = getInfo('pageInfo.csv', 'myWeek')
    date_now = datetime.now()
    user_id = current_user.id
    sida, sub_menu = common_route('Min Vecka', ['/pmg/month', '/pmg/week', '/pmg/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])

    start_week = date_now - timedelta(days=date_now.weekday())
    end_week = start_week + timedelta(days=6)

    activities = get_activities_for_user(current_user.id, start_week, end_week)
    activities_dict = organize_activities_by_time(activities)

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
        Score.Date >= start_week
    ).filter(
        Score.Date <= end_week
    ).filter(
        Score.user_id == user_id
    ).all()
    weekly_data = process_weekly_scores(myScore, start_week, end_week)

    return render_template('pmg/myWeek.html', sida='Veckoplanering', weekly_data=weekly_data, header='Veckoplanering',
                           total_score=0, sub_menu=sub_menu, activities=activities_dict,page_info=page_info)

@pmg_bp.route('/timebox', methods=['GET', 'POST'])
@login_required
def timebox():
    page_info = getInfo('pageInfo.csv', 'myDay')
    current_date = datetime.now().strftime("%Y-%m-%d")
    today = datetime.now()
    viktigt = Idag.query.filter_by(date=today, user_id=current_user.id).all()
    tankar = Idag.query.filter_by(date=today, user_id=current_user.id).all()

    sida, sub_menu = common_route('Min Dag', ['/pmg/month', '/pmg/week', '/pmg/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])
    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    activities = get_activities_for_user(current_user.id, start_date, end_date)
    activities_dict = organize_activities_by_time(activities)

    if request.method == 'POST':
        viktig_list = []
        tankar_list = []

        for i in range(1, 6):
            viktig = request.form.get(f'viktig_{i}')
            tanke = request.form.get(f'tankar_{i}')

            if viktig:
                viktig_list.append(viktig)
            if tanke:
                tankar_list.append(tanke)

        # Kombinera listorna till en enda sträng
        viktig_str = ",".join(viktig_list)
        tankar_str = ",".join(tankar_list)

        # Spara strängarna i databasen
        ny_viktig_punkt = Idag(date=current_date, viktigt=viktig_str, user_id=current_user.id)
        ny_tanke = Idag(date=current_date, tankar=tankar_str, user_id=current_user.id)
        db.session.add(ny_viktig_punkt)
        db.session.add(ny_tanke)
        db.session.commit()

        return redirect(url_for('pmg.timebox'))

    # Hämta sparade punkter
    saved_entry = Idag.query.filter_by(date=current_date, user_id=current_user.id).first()
    if saved_entry:
        viktigt_saved = saved_entry.viktigt.split(",") if saved_entry.viktigt else []
        tankar_saved = saved_entry.tankar.split(",") if saved_entry.tankar else []
    else:
        viktigt_saved = [""] * 5
        tankar_saved = [""] * 5
    return render_template('pmg/timebox.html', current_date=current_date, sida=sida,
                           header=sida, sub_menu=sub_menu, activities=activities_dict,
                           page_info=page_info, viktigt_saved=viktigt_saved, tankar_saved=tankar_saved)

# endregion

#region Journal
@pmg_bp.route('/journal', methods=['GET', 'POST'])
def journal():
    section_name = request.args.get('section_name')
    my_act = Activity.query.filter_by(name=section_name, user_id=current_user.id).all()
    activity_names = [act.name for act in my_act]
    if not section_name:
        return redirect(url_for('pmg.journal', section_name='Mina Ord'))

    if section_name == 'Mina Ord' or section_name == 'skriva':
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Ord", [url_for('pmg.journal', section_name='skriva'),
                                                   url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    if section_name == 'Mina Mål':
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Mål", [url_for('pmg.journal', section_name='skriva'),
                                                   url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    elif section_name == "Bullet" or section_name == "Lista":
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Bullet", [url_for('pmg.journal', section_name='skriva'),
                                                 url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

    elif section_name in activity_names:
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route(section_name, [url_for('pmg.journal', section_name='skriva'),
                                                     url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

    elif section_name == 'blogg':
        sida, sub_menu = common_route("Blogg", [url_for('pmg.journal', section_name='skriva'),
                                                url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = BloggPost.query.filter_by(user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)

    else:
        sida, sub_menu = common_route(section_name, [url_for('pmg.journal', section_name='skriva'),
                                                     url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = BloggPost.query.filter_by(title=section_name, user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)

@pmg_bp.route('/journal/<section_name>', methods=['GET', 'POST'])
def journal_section(act_id, sida, sub_menu, my_posts):
    page_info = getInfo('pageInfo.csv', sida)
    current_date = date.today()
    why_G = ""
    page_url = 'pmg.journal'
    activities = None
    ordet,ord_lista = getWord()

    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet,ord_lista = getWord()

    if sida == 'Dagbok':
        ordet = current_date
    elif sida == 'Mina Mål':
        goals = Goals.query.filter_by(user_id=current_user.id).with_entities(Goals.name).all()
        used_goals = WhyGoals.query.filter_by(user_id=current_user.id).with_entities(WhyGoals.goal).all()
        goal_list = [goal[0] for goal in goals]
        used_goal_list = [used_goal[0] for used_goal in used_goals]
        for goal in goal_list:
            if not goal in used_goal_list:
                ordet = f'Varför är detta mål viktigt för dig? ({goal})'
                why_G = goal
            break
    elif sida == "Bullet":
        ordet = ['Tacksam för', 'Inför imorgon', "Personer som betyder",
                 'Distraherar mig', 'Motiverar mig',
                 'Jag borde...', 'Värt att fundera på', 'Jag ska försöka..']

    time = Settings.query.filter_by(user_id=current_user.id).first().stInterval
    if not time:
        time = 15
    titles = []  # Initialisera titles här för att säkerställa att den alltid har ett värde

    if act_id is not None:
        print(act_id)
        myGoals = Goals.query.filter_by(name="Skriva", user_id=current_user.id).first()
        if myGoals:
            activities = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles_list = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles = [item.name for item in titles_list]
    elif act_id is None:
        myGoals = None
        activities = None
        titles_list = BloggPost.query.filter_by(user_id=current_user.id).distinct().with_entities(BloggPost.title).all()
        titles = [item[0] for item in titles_list]

    if request.method == 'POST':
        option = request.form.get('option')
        print(option)
        user = User.query.filter_by(id=current_user.id).first()
        content_check = request.form['blogg-content']
        if content_check:
            if option == 'timeless':
                if sida == 'Dagbok':
                    add2db(Dagbok, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Mina Ord':
                    add2db(BloggPost, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Bullet':
                    theme = request.form['post-ord']
                    bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'], request.form['#5']]
                    newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list, date=current_date, user_id=current_user.id)
                    db.session.add(newBullet)
                    db.session.commit()
                elif sida == 'Mina Mål':
                    add2db(WhyGoals,request,['post-ord','blogg-content','goal'],['title','text','goal'],user)
            elif option == "write-on-time":
                add2db(Score, request, ['gID', 'aID', 'aDate', 'score'], ['Goal', 'Activity', 'Date', 'Time'], user)
                if sida == 'Dagbok':
                    add2db(Dagbok, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Mina Ord':
                    add2db(BloggPost, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Bullet':
                    theme = request.form['post-ord']
                    bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'],
                                   request.form['#5']]
                    newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list,
                                       date=current_date, user_id=current_user.id)
                    db.session.add(newBullet)
                    db.session.commit()

                update_dagar(current_user.id,Dagar)
    return render_template('pmg/journal.html', time=time, goal=myGoals, activities=activities, side_options=titles,
                           ordet=ordet, sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu,
                           current_date=current_date, page_url=page_url, act_id=act_id, myPosts=my_posts,
                           page_info=page_info, why_G=why_G)

@pmg_bp.route('/get-new-word')
def get_new_word(section_id):
    ordet = None
    ordet,ord_lista = getWord()
    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet, ord_lista = getWord()

    return jsonify(ordet)
# endregion

# region Settings
@pmg_bp.route('/settings/<section_name>', methods=['GET', 'POST'])
@pmg_bp.route('/settings', methods=['GET', 'POST'])
def settings(section_name=None):
    if not section_name:
        section_name = request.args.get('section_name', 'general')
    sida, sub_menu = common_route('Settings', [
        url_for('pmg.settings', section_name='timer'),
        url_for('pmg.settings', section_name='skrivande'),
        url_for('pmg.settings', section_name='konto')
    ], ['Timer', 'Journal', 'Konto'])

    if section_name == 'timer':
        sida = 'Timer-inställningar'
        page_info = getInfo('pageInfo.csv', 'Time-Settings')

    elif section_name == 'skrivande':
        sida = 'Blogg-inställningar'
        page_info = getInfo('pageInfo.csv', 'Text-Settings')
        Sett = Settings.query.filter_by(user_id=current_user.id).first()

        if not Sett.wImp:
            ordet, ord_lista = readWords('orden.txt')
            for ord in ord_lista:
                # Kontrollera om ordet redan finns i MyWords för den specifika användaren
                existing_word = MyWords.query.filter_by(ord=ord, user_id=current_user.id).first()
                if not existing_word:
                    nyttOrd = MyWords(ord=ord, user_id=current_user.id)
                    db.session.add(nyttOrd)
                    db.session.commit()
                stInt = Settings.query.filter_by(user_id=current_user.id).first()
                stInt.wImp = True
                db.session.commit()
    elif section_name == 'konto':
        sida = 'Konto-inställningar'
        page_info = getInfo('pageInfo.csv', 'Account-Settings')
    else:
        sida = 'Allmänna Inställningar'
        page_info = getInfo('pageInfo.csv', 'Settings')

    mina_Ord = query(MyWords, 'user_id', current_user.id)

    if request.method == 'POST':
        action = request.form['action']
        if action == 'password':
            user = User.query.filter_by(id=current_user.id).first()

            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not check_password_hash(user.password, current_password):
                flash('Felaktigt nuvarande lösenord.', 'danger')
                return render_template('pmg/settings.html', sida="Konto-inställningar",header="Konto-inställningar",my_words=mina_Ord,
                           sub_menu=sub_menu, page_info=page_info, user=current_user)

            if new_password != confirm_new_password:
                flash('De nya lösenorden matchar inte.', 'danger')
                return render_template('pmg/settings.html', sida="Konto-inställningar",header="Konto-inställningar",my_words=mina_Ord,
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
            return render_template('pmg/settings.html', sida=sida, header=sida, my_words=mina_Ord,
                                   sub_menu=sub_menu, page_info=page_info, user=current_user)

    return render_template('pmg/settings.html', sida=sida, header=sida, my_words=mina_Ord,
                           sub_menu=sub_menu, page_info=page_info, user=current_user)

# endregion