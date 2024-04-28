from flask import Blueprint, render_template, redirect, url_for, request
from models import User, db,Streak,BloggPost,Goals
from datetime import datetime, timedelta
pmg_bp = Blueprint('pmg', __name__, template_folder='templates')

#region PMG
@pmg_bp.route('/streak',methods=['GET', 'POST'])
def streak():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida="Mina Streaks"
    myStreaks = Streak.query.all()
    print(myStreaks)
    if request.method == 'POST':
        Streak_name = request.form['streakName']
        Streak_dayOne = request.form['streakStart']
        Streak_priority = request.form['streakPriority']
        Streak_condition = request.form['streakConditions']
        newStreak = Streak(name=Streak_name, priority=Streak_priority, count=1,
                           best=1,condition=Streak_condition, lastReg=Streak_dayOne,
                           dayOne=Streak_dayOne)

        db.session.add(newStreak)
        db.session.commit()
        return redirect(url_for('streak'),sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)
    return render_template('streak.html',sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)

@pmg_bp.route('/goals',methods=['GET', 'POST'])
def goals():
    myGoals = Goals.query.all()
    sida = "Mina Mål"
    return render_template('goals.html',sida=sida,header=sida, goals=myGoals)

@pmg_bp.route('/myday')
def myday():
    sida = "Min Dag"
    return render_template('myday.html',sida=sida,header=sida)

@pmg_bp.route('/month')
def month():
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
    return render_template('month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida)
# endregion