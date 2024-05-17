from random import choice
import plotly.graph_objects as go
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from models import User, db, Streak, BloggPost, Goals, Activity, Score, MyWords,Settings
from datetime import datetime, timedelta
from flask_login import current_user
import pandas as pd

pmg_bp = Blueprint('pmg', __name__, template_folder='templates')

#region PMG
def read(filename):
    with open(filename,'r') as file:
        data = file.read()
    data = data.split('\n')
    data_ord = choice(data)
    return data_ord,data
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
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Iterera över form_fields och model_fields och sätt attribut på new_entry
    for form_fields, model_field in zip(form_fields, model_fields):
        setattr(new_entry, model_field, request.form[form_fields])

    # Lägg till user_id om det är en del av modellen
    if hasattr(new_entry, 'user_id'):
        setattr(new_entry, 'user_id', user.id)
    if hasattr(new_entry, 'date'):
        setattr(new_entry, 'date', current_date)
    if hasattr(new_entry, 'author'):
        setattr(new_entry, 'author', user.username)
    # Lägg till den nya posten i sessionen och committa
    db.session.add(new_entry)
    db.session.commit()

def query(db, key, filter):
    return db.query.filter_by(**{key: filter}).all()

def unique(db,by_db):
    unique_data = [post.title for post in db.query.with_entities(by_db).distinct().all()]
    print(unique_data)
    list = [item[0] for item in unique_data]
    return list

def section_content(db,section):
    list = db.query.filter_by(name=section).first()
    return list.id
@pmg_bp.route('/timer')
def timer():
    sida='Timer'
    duration = request.args.get('duration', default=60, type=int)
    return render_template('timer.html',sida=sida,
                           header=sida, duration=duration)
@pmg_bp.route('/streak',methods=['GET', 'POST'])
def streak():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida="Mina Streaks"

    myStreaks = query(Streak,'user_id',current_user.id)

    if request.method == 'POST':
        form_fields = ['streakName','streakInterval','streakCount',
                       'streakGoal','streakBest','streakCondition',
                       'streakLast','streakStart']
        model_fields = ['name', 'interval', 'count',
                        'goal','best','condition',
                        'lastReg','dayOne']
        add2db(Streak, request, form_fields, model_fields, current_user.id)

        return redirect(url_for('pmg.streak'))
    return render_template('streak.html',sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)
@pmg_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = datetime.utcnow().strftime('%Y.%m.%d')
    if action == 'check':
        if today != streak.lastReg:
            count = streak.count
            best_now = streak.best
            count += 1
            if best_now < count:
                best_now = count
                streak.best = best_now
            streak.count = count
            streak.lastReg = today
            db.session.commit()

    elif action == 'cross':
        streak.count = 0
        streak.day_one = today  # Reset the start day of the streak
        streak.lastReg = today
        db.session.commit()

    return redirect(url_for('pmg.myday'))
@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    # Ensures that only activities for the current user and specific goal are fetched
    activities = Activity.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]
    return jsonify(activity_list)

@pmg_bp.route('/goals',methods=['GET', 'POST'])
def goals():

    myGoals = query(Goals,'user_id',current_user.id)
    sida,sub_menu = common_route('My Goals',None,None)

    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            add2db(Goals, request, ['goalName'], ['name'], current_user.id)
            return redirect(url_for('pmg.goals', sida=sida, header=sida, goals=myGoals))

        elif 'addActivity' in request.form['action']:
            add2db(Activity, request, ['goalId','activity-name','activity-measurement'],
                   ['goal_id','name','measurement'], current_user.id)
            return redirect(url_for('pmg.goals',sida=sida,header=sida, goals=myGoals))

    return render_template('goals.html',sida=sida,header=sida, goals=myGoals)

@pmg_bp.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    # Data från JSON-kroppen, om du behöver den
    data = request.get_json()
    print(data)  # Debug: se vad som faktiskt tas emot

    goal = Goals.query.get(goal_id)
    if goal:
        db.session.delete(goal)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False)

def myDayScore(date):
    total = 0
    myScore = db.session.query(
        Goals.name.label('goal_name'),
        Activity.name.label('activity_name'),
        Score.Date,
        Score.Time
    ).join(
        Goals, Goals.id == Score.Goal
    ).join(
        Activity, Activity.id == Score.Activity
    ).filter(Score.Date == date).all()

    for score in myScore:
        total += float(score.Time)

    return myScore,total


# noinspection PyTypeChecker
@pmg_bp.route('/myday', methods=['GET','POST'])
def myday():
    date_now = datetime.now().strftime('%Y.%m.%d')
    sida = "Min Dag"
    myGoals = query(Goals,'user_id',current_user.id)
    myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != date_now).all()
    myScore = query(Score,'user_id',current_user.id)
    myScore,total = myDayScore(date_now)
    for score in myScore:
        print(score)
    sorted_myScore = sorted(myScore, key=lambda score: score[0])
    df = pd.DataFrame(sorted_myScore, columns=['goal', 'activity', 'date', 'score'])

    # Plotta aggregerad data
    fig = go.Figure(data=[go.Bar(x=df['goal'], y=df['score'])])
    # Justera storleken på plotten och uppdatera layouten
    fig.update_layout(
        title_text='Total Score per Goal',
        xaxis_title='Goal',
        yaxis_title='Total Score',
        plot_bgcolor='white',
        showlegend=False,
        width=400,  # bredd på plotten
        height=300  # höjd på plotten
    )
    # För att bädda in figuren på en webbsida kan du använda Plotly's to_html() funktion
    html_string = fig.to_html(full_html=False, include_plotlyjs='cdn')

    if request.method == 'POST':
        add2db(Score,request,['gID','aID','aDate','score'],
               ['Goal','Activity','Date','Time'], current_user.id)
        return redirect(url_for('pmg.myday'))

    return render_template('myday.html',sida=sida,header=sida, current_date=date_now,
                           my_goals=myGoals, my_streaks=myStreaks, my_score=myScore,total_score=total,plot=html_string)

@pmg_bp.route('/myday/<date>')
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
    today = datetime.now().date()

    myGoals = query(Goals, 'user_id', current_user.id)
    myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != today).all()
    myScore = query(Score, 'user_id', current_user.id)
    myScore, total = myDayScore(selected_date)

    if selected_date < today:
        sida='Past Day'
        return render_template('pastDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    elif selected_date > today:
        sida = 'Post Day'
        return render_template('postDays.html', sida=sida, header=sida, current_date=selected_date,
                               my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
    else:
        return redirect(url_for('pmg.myday'))

@pmg_bp.route('/week')
def week():
    sida='My Week'
    return render_template('myWeek.html',sida=sida, header=sida)
@pmg_bp.route('/month')
@pmg_bp.route('/month/<int:year>/<int:month>')
def month(year=None, month=None):
    sida, sub_menu = common_route('Kalender',['/pmg/month/','/pmg/week/','/pmg/myday/'],['Min Månad','Min Vecka','Min Dag'])
    # Det nuvarande året och månaden
    if not year or not month:
        year = datetime.now().year
        month = datetime.now().month

    first_day_of_month = datetime(year, month, 1)
    month_name = first_day_of_month.strftime('%B')

    # Skapa en lista som representerar dagarna i månaden, inklusive föregående och nästkommande månad
    days = []
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

    # Dela upp dagarna i veckor
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    # Titeln och headern för sidan
    sida = "Min Kalender"

    return render_template('month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida, sub_menu=sub_menu, month=month, days=days)

@pmg_bp.route('/journal', methods=['GET', 'POST'])
def journal():
    section_name = request.args.get('section_name')
    my_act = Activity.query.filter_by(name=section_name, user_id=current_user.id).all()
    activity_names = [act.name for act in my_act]

    if section_name == 'Mina Ord' or section_name == 'skrivande':
        act_id = 1
        sida, sub_menu = common_route("Mina Ord", [url_for('pmg.journal', section_name='skrivande'),
                                                   url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    elif section_name in activity_names:
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route(section_name, [url_for('pmg.journal', section_name='skrivande'),
                                                     url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

    elif section_name == 'blogg':
        sida, sub_menu = common_route("Blogg", [url_for('pmg.journal', section_name='skrivande'),
                                                url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = BloggPost.query.filter_by(user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)

    else:
        sida, sub_menu = common_route(section_name, [url_for('pmg.journal', section_name='skrivande'),
                                                     url_for('pmg.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = BloggPost.query.filter_by(title=section_name, user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)
@pmg_bp.route('/journal/<section_name>', methods=['GET', 'POST'])
def journal_section(act_id, sida, sub_menu, my_posts):
    current_date = datetime.now().strftime("%Y-%m-%d")
    page_url = 'pmg.journal'
    activities = None
    ordet, ord_lista = read('orden.txt')
    time = Settings.query.filter_by(user_id=current_user.id).first().stInterval
    if act_id is not None:
        myGoals = Goals.query.filter_by(name='Skriva', user_id=current_user.id).first()
        if myGoals:
            activities = Activity.query.filter_by(goal_id=myGoals.id).all()
            titles_list = Activity.query.filter_by(goal_id=myGoals.id).all()
            titles = [item.name for item in titles_list]
            option = request.form.get('option')
            if request.method == 'POST':
                user = User.query.filter_by(id=current_user.id).first()
                if option == 'timeless':
                    add2db(BloggPost, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif option == "time":
                    add2db(Score, request, ['gID', 'aID', 'aDate', 'score'], ['Goal', 'Activity', 'Date', 'Time'], user)
                    add2db(BloggPost, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)

    elif act_id is None:
        myGoals = None
        activities = None
        titles_list = BloggPost.query.filter_by(user_id=current_user.id).distinct().with_entities(BloggPost.title).all()
        titles = [item[0] for item in titles_list]
        print(titles)
    return render_template('journal.html', time=time, goal=myGoals, activities=activities, side_options=titles,
                           ordet=ordet, sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu,
                           current_date=current_date, page_url=page_url, act_id=act_id, myPosts=my_posts)
@pmg_bp.route('/get-new-word')
def get_new_word(section_id):
    orden = MyWords.query.filter_by(user_id=current_user.id).with_entities(MyWords.ord).all()
    if orden:
        ord_lista = [ord[0] for ord in orden]
        ordet = choice(ord_lista)
    else:
        ordet,ord_lista=read('orden.txt')
    return jsonify(ordet)
@pmg_bp.route('/settings',methods=['GET','POST'])
def settings():
    sida, sub_menu = common_route('Inställningar',['/pmg/settings','/pmg/settings/timer','/pmg/konto'],['Journal','Timer','Konto'])
    mina_Ord = query(MyWords,'user_id',current_user.id)
    if request.method == 'POST':

        if "word" in request.form['action']:
            add2db(MyWords,request,['nytt-ord'],['ord'], current_user.id)
            return redirect(url_for('pmg.settings'))

        elif "timer" in request.form['action']:
            existing_setting = Settings.query.filter_by(user_id=current_user.id).first()
            if existing_setting:
                intervall = request.form['time-intervall']
                existing_setting.stInterval = int(intervall)
                db.session.commit()
            else:
                add2db(Settings, request, ['time-intervall'],
                       ['stInterval'], current_user.id)
            return redirect(url_for('pmg.myday'))

    return render_template('settings.html', sida=sida, header=sida, my_words=mina_Ord,sub_menu=sub_menu)
# endregion