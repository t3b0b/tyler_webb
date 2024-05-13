from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from models import User, db, Streak, BloggPost, Goals, Activity, Score, MyWords,Settings
from datetime import datetime, timedelta
from flask_login import current_user
from morgontext import headings
pmg_bp = Blueprint('pmg', __name__, template_folder='templates')

#region PMG
@pmg_bp.route('/streak',methods=['GET', 'POST'])
def streak():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida="Mina Streaks"
    myStreaks = Streak.query.filter_by(user_id=current_user.id).all()
    print(myStreaks)
    if request.method == 'POST':
        Streak_name = request.form['streakName']
        Streak_dayOne = request.form['streakStart']
        Streak_priority = request.form['streakPriority']
        Streak_condition = request.form['streakConditions']
        newStreak = Streak(name=Streak_name, priority=Streak_priority, count=1,
                           best=1,condition=Streak_condition, lastReg=Streak_dayOne,
                           dayOne=Streak_dayOne,user_id=current_user.id)
        db.session.add(newStreak)
        db.session.commit()
        return redirect(url_for('pmg.streak'))
    return render_template('streak.html',sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)

@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    # Ensures that only activities for the current user and specific goal are fetched
    activities = Activity.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]
    return jsonify(activity_list)

@pmg_bp.route('/goals',methods=['GET', 'POST'])
def goals():
    myGoals = Goals.query.filter_by(user_id=current_user.id).all()
    sida = "Mina Mål"
    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            goal_name = request.form['goalName']
            newGoal = Goals(name=goal_name,user_id=current_user.id)
            db.session.add(newGoal)
            db.session.commit()
            return redirect(url_for('pmg.goals', sida=sida, header=sida, goals=myGoals))
        elif 'addActivity' in request.form['action']:
            goal_id= request.form['goalId']
            activity_name = request.form['activity-name']
            activity_measurement = request.form['activity-measurement']
            newActivity = Activity(goal_id=goal_id,name=activity_name,
                                   measurement=activity_measurement, user_id=current_user.id)
            db.session.add(newActivity)
            db.session.commit()
            return redirect(url_for('pmg.goals',sida=sida,header=sida, goals=myGoals))
    return render_template('goals.html',sida=sida,header=sida, goals=myGoals)

@pmg_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = datetime.utcnow().strftime('%Y.%m.%d')
    if action == 'check':
        if today != streak.lastReg:
            count = streak.count
            count += 1
            streak.count = count
            streak.lastReg = today
            db.session.commit()

    elif action == 'cross':
        streak.count = 0
        streak.day_one = today  # Reset the start day of the streak
        db.session.commit()

    return redirect(url_for('pmg.myday'))

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

@pmg_bp.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    goal = Goals.query.get(goal_id)
    if goal:
        db.session.delete(goal)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 404

@pmg_bp.route('/myday', methods=['GET','POST'])
def myday():
    date_now = datetime.now().strftime('%Y.%m.%d')
    sida = "Min Dag"
    myGoals = Goals.query.filter_by(user_id=current_user.id).all()
    myStreaks = Streak.query.filter_by(user_id=current_user.id).all()
    myScore = Score.query.filter_by(user_id=current_user.id).all()
    myScore,total = myDayScore(date_now)
    if request.method == 'POST':
        goal_id = request.form['gID']
        activity_id = request.form['aID']
        activity_date = request.form['aDate']
        activity_score = request.form['score']
        new_score = Score(Goal=goal_id, Activity=activity_id,Date=activity_date,Time=activity_score,user_id=current_user.id)
        db.session.add(new_score)
        db.session.commit()
        return redirect(url_for('pmg.myday'))
    return render_template('myday.html',sida=sida,header=sida, current_date=date_now,
                           my_goals=myGoals, my_streaks=myStreaks, my_score=myScore,total_score=total)

@pmg_bp.route('/myday/<date>')
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y.%m.%d')
    sida = "Min Dag"
    myGoals = Goals.query.filter_by(user_id=current_user.id).all()
    myStreaks = Streak.query.filter_by(user_id=current_user.id).all()
    myScore=Score.query.filter_by(user_id=current_user.id).all()
    myScore, total = myDayScore(selected_date)
    return render_template('myday.html', sida=sida, header=sida, current_date=selected_date,
                           my_goals=myGoals, my_streaks=myStreaks, my_score=myScore, total_score=total)
@pmg_bp.route('/month')
def month():
    sub_menu = [
        {'choice': '/pmg/month', 'text': 'Månad'},
        {'choice': '/pmg/week', 'text': 'Vecka'},
        {'choice': '/pmg/myday', 'text': 'Dag'}
    ]
    # Det nuvarande året och månaden
    year = datetime.now().year
    month = datetime.now().month

    # Första dagen i månaden och månadens namn
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
    sida = "Min Månad"
    return render_template('month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida, sub_menu=sub_menu)

@pmg_bp.route('/journal/skrivande', methods=['GET', 'POST'])
def journal():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida = "Skrivande"
    sub_menu = [
        {'choice': '/pmg/journal/skrivande', 'text': 'Skriv'},
        {'choice': '/pmg/journal/läs', 'text': 'Blogg'},
    ]
    orden = MyWords.query.filter_by(user_id=current_user.id).with_entities(MyWords.ord).all()
    ord_lista=[ord[0] for ord in orden]
    print(ord_lista)
    if request.method == 'POST':
        post_author = User.query.filter_by(id=current_user.id).first().username
        post_ord = request.form['post-ord']
        post_text = request.form['blogg-content']
        post_date = current_date
        newPost = BloggPost(author=post_author, title=post_ord,
                            content=post_text, date=post_date, user_id=current_user.id)
        db.session.add(newPost)
        db.session.commit()

    return render_template('journal.html', sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu)
@pmg_bp.route('/journal/läs')
def read_journal():
    sida = "Blogg"
    myPosts = BloggPost.query.filter_by(user_id=current_user.id).all()
    sub_menu = [
        {'choice': '/pmg/journal/skrivande', 'text': 'Skriv'},
        {'choice': '/pmg/journal/läs', 'text': 'Blogg'},
    ]
    return render_template('journal.html',sida=sida, header=sida,sub_menu=sub_menu,myPosts=myPosts)

@pmg_bp.route('/settings',methods=['GET','POST'])
def settings():
    sub_menu = [
        {'choice': '/pmg/settings', 'text': 'Journal'},
        {'choice': '/pmg/settings', 'text': 'Timer'},
        {'choice': '/pmg/settings', 'text': 'Konto'}
    ]
    for head in headings:
        ordet=head
        newWord = MyWords(ord=ordet, user_id=current_user.id)
        db.session.add(newWord)
        db.session.commit()

    sida = 'Inställningar'
    myWords=MyWords.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        if "word" in request.form['action']:
            ord = request.form['nytt-ord']
            newWord = MyWords(ord=ord,user_id=current_user.id)
            db.session.add(newWord)
            db.session.commit()
            return redirect(url_for('pmg.settings'))
        elif "timer" in request.form['action']:
            intervall=request.form['time-intervall']
            newsetting=Settings(stInterval=intervall)
            db.session.add(newsetting)
            db.session.commit()
            return redirect(url_for('pmg.myday'))
    return render_template('settings.html', sida=sida, header=sida, my_words=myWords)
# endregion