from random import choice
from extensions import db
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from sqlalchemy.orm import aliased
from models import (Streak, Goals,Activity, Score,Event,TopFive)

from datetime import datetime, timedelta

from pmg_func import (getSwetime,common_route,filter_mod)
from classes.calHandler import Calendar,UserCalendar
from flask_login import current_user, login_required

from classes.scoreHandler import ScoreAnalyzer,UserScores
from classes.calHandler import Calendar

cal_bp = Blueprint('cal', __name__, template_folder='templates/cal')

cal = Calendar()
scoreHandler = ScoreAnalyzer()

#region Milestones
@cal_bp.route('milestones/<int:goal_id>')
@login_required
def milestones(goal_id):
    return render_template('pmg/milestones.html')

@cal_bp.route('/myday/<date>')
@login_required
def myday_date(date):
    analyzer = UserScores(current_user.id)
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    session = scoped_session(db.session)
    now = getSwetime()
    today = now.date()

    with session.begin():
        myGoals = filter_mod(Goals, user_id = current_user.id)
        myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != today).all()
        myScore, total = analyzer.myDayScore(selected_date, current_user.id)

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
def get_daily_summary(user_id, date=None):
    """
    Hämtar summering av dagens poäng, streaks och avklarade streaks.
    Om datum inte anges används dagens datum.
    """
    if date is None:
        date = datetime.now().date()  # Använd lokal tid istället för UTC

    # 🏆 Hämta totalpoäng från Score-tabellen för angivet datum
    total_points = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        Score.Date == date
    ).scalar() or 0  # Om ingen data, sätt 0

    # 🔥 Hämta totalt antal streaks
    total_streaks = Streak.query.filter_by(user_id=user_id).count()

    # ✅ Hämta antal avklarade streaks (de som har `active=False` och uppdaterades idag)
    completed_streaks = db.session.query(db.func.count(db.distinct(Score.Streak))).filter(
        Score.user_id == user_id,
        Score.Date == date,
    ).scalar() or 0

    # 🏅 Hämta namn på avklarade streaks
    completed_streaks_names = db.session.query(Streak.name).join(Score).filter(
        Score.user_id == user_id,
        Score.Date == date,
    ).distinct().all()

    return {
        "date": date,
        "total_points": total_points,
        "total_streaks": total_streaks,
        "completed_streaks": completed_streaks,
        "completed_streaks_names": completed_streaks_names
    }

#region Kalender

@cal_bp.route('/save_calendar_bullet/<date>/<view_type>', methods=['POST'])
@login_required
def save_calendar_bullet(date, view_type):
    # Hämta användarens CalendarBullet för det aktuella datumet
    calendar_bullet = TopFive.query.filter_by(user_id=current_user.id, date=date).first()

    # Om det inte finns någon bullet för det datumet, skapa en ny
    if not calendar_bullet:
        calendar_bullet = TopFive(user_id=current_user.id, date=date)

    # Hämta data från formuläret
    calendar_bullet.to_do = request.form.get('to_do')
    calendar_bullet.to_think = request.form.get('to_think')
    calendar_bullet.remember = request.form.get('remember')

    # Ställ in view_type från URL-parametern

    # Lägg till eller uppdatera i databasen
    db.session.add(calendar_bullet)
    db.session.commit()

    flash('Dagens anteckningar har sparats!', 'success')
    return redirect(url_for('cal.' + view_type))  # Omdirigera till motsvarande vy

@cal_bp.route('/day/<string:date>', methods=['GET', 'POST'])
@login_required
def day_view(date):
    userCal = UserCalendar(current_user.id)
    # Konvertera `date` från sträng till datetime-objekt
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        flash("Ogiltigt datumformat. Använd 'YYYY-MM-DD'.", 'danger')
        return redirect(url_for('cal.month_view'))
    
    myGoals=Goals.query.filter_by(user_id=current_user.id)

    events = userCal.get_events_for_day(date)

    # Strukturera data för mallen
    event_data = []
    for event, goal_name in events:
        event_data.append({
            "event_id": event.id,
            "event_name": event.name,
            "start_time": event.start_time.strftime('%H:%M') if event.start_time else None,
            "end_time": event.end_time.strftime('%H:%M') if event.end_time else None,
            "location": event.location,
            "goal_id": event.goal_id,
            "goal_name": goal_name or "Okänt mål"
        })

    if request.method == 'POST':
        event_name = request.form.get('event-name')
        event_type = request.form.get('eventType')
        start_time = request.form.get('event-start')
        end_time = request.form.get('event-end')
        location = request.form.get('event-location')
        goal_id = request.form.get('goal-id')
        activity_id = request.form.get('activity-id')  # Här hämtar du den valda aktiviteten

        is_recurring = request.form.get('is-recurring') == 'true'
        recurrence_type = request.form.get('recurrance-type')
        recurrence_interval = int(request.form.get('recurrance-interval') or 1)

        if event_name and event_type and start_time:
            new_event = Event(
                name=event_name,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                location=location,
                date=date,
                user_id=current_user.id,
                goal_id=goal_id if goal_id else None,
                activity_id=activity_id if activity_id else None,
                is_recurring=is_recurring,
                recurrence_type=recurrence_type if is_recurring else None,
                recurrence_interval=recurrence_interval if is_recurring else None
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event added successfully!', 'success')
        else:
            flash('Please provide all required fields.', 'danger')

        return redirect(url_for('cal.day_view', date=date.strftime('%Y-%m-%d')))

    return render_template('cal/day_view.html', date=date,events=event_data, goals=myGoals)

@cal_bp.route('/month', methods=['GET', 'POST'])
@cal_bp.route('/month/<int:year>/<int:month>')
@login_required
def month(year=None, month=None):

    sida, sub_menu = common_route('Min Månad', ['/cal/month', '/cal/week', '/cal/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])

    if not year or not month:
        year = datetime.now().year
        month = datetime.now().month

    first_day_of_month = datetime(year, month, 1)
    month_name = first_day_of_month.strftime('%B')

    weeks = cal.generate_calendar_weeks(year, month)

    sida = "Min Kalender"
    today = datetime.now()
    today_date = datetime(today.year, today.month, today.day, 0, 0, 0)

    # 🔄 Hämta dagliga sammanfattningar för hela månaden
    dag_data = {}
    for week in weeks:
        for day in week:
            date_str = day['date'].strftime('%Y-%m-%d')
            dag_data[date_str] = get_daily_summary(current_user.id, day['date'])

    return render_template('cal/month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida,
                           sub_menu=sub_menu, month=month, today_date=today_date, dag_data=dag_data)

def prepWeekData(scores):
    """
    Konverterar score-objekt till en struktur med 'start_hour' och 'duration_in_hours'.
    """
    processed = {}

    for score in scores:
        date_str = score.Date.strftime('%Y-%m-%d')
        if date_str not in processed:
            processed[date_str] = []

        start_hour = score.Start.hour + score.Start.minute / 60
        duration = score.Time / 60  # omvandla till timmar

        processed[date_str].append({
            'activity_name': score.activity_name,
            'Start': score.Start,
            'End': score.End,
            'duration_hours': duration,
            'minutes': score.Time
        })

    return processed

@cal_bp.route('/week', methods=['GET', 'POST'])
@login_required
def week():
    current_date = datetime.now()
    year, week_num, weekday = current_date.isocalendar()
    start_week = current_date - timedelta(days=current_date.weekday())  # Start of the current week
    end_week = start_week + timedelta(days=6)  # End of the current week
    user_id = current_user.id
    sida, sub_menu = common_route('Min Vecka', ['/cal/month', '/cal/week', '/cal/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])

    # Generera alla datum för veckan som en lista av strängar
    week_dates = [(start_week + timedelta(days=day)).strftime('%Y-%m-%d') for day in range(7)]

    # Fetch all scores for the user during the week
    scores = db.session.query(
        Activity.name.label('activity_name'),
        Score.Start,
        Score.End,
        Score.Time,
        Score.Date
    ).join(
        Activity, Activity.id == Score.Activity
    ).filter(
        Score.user_id == user_id
    ).filter(
        Score.Date >= start_week.date()
    ).filter(
        Score.Date <= end_week.date()
    ).all()

    # Organize scores by day and hour
    week_scores = {date: [] for date in week_dates}  # Initiera alla datum i veckan med tomma listor
    
    weekData = prepWeekData(scores)

    for score in scores:
        day_str = score.Date.strftime('%Y-%m-%d')
        week_scores[day_str].append(score)
        print(f"Added score: {score.activity_name} to {score.Date} from {score.Start} to {score.End}")

    bullet = TopFive.query.filter_by(user_id=current_user.id).first()

    # Om det inte finns något, skapa ett nytt objekt
    if not bullet:
        bullet = TopFive(user_id=current_user.id)
        db.session.add(bullet)

    # Om POST-förfrågan skickas, uppdatera listorna
    today = current_date.date()
    if request.method == 'POST':
        # Spara To-Do listan
        if 'save_todo' in request.form:
            todo_list = [request.form.get(f'todo_{i}') for i in range(1, 6) if request.form.get(f'todo_{i}')]
            # Skapa en ny post med titel "To-Do" och spara listan som innehåll
            todo_bullet = TopFive(title='To-Do', content=','.join(todo_list), user_id=current_user.id,
                                  date=today)
            db.session.add(todo_bullet)
            db.session.commit()
        # Spara Think listan
        if 'save_think' in request.form:
            think_list = [request.form.get(f'think_{i}') for i in range(1, 6) if request.form.get(f'think_{i}')]
            think_bullet = TopFive(title='Think', content=','.join(think_list), user_id=current_user.id,
                                   date=today)
            db.session.add(think_bullet)
            db.session.commit()
        # Spara Remember listan
        if 'save_remember' in request.form:
            remember_list = [request.form.get(f'remember_{i}') for i in range(1, 6) if
                             request.form.get(f'remember_{i}')]
            remember_bullet = TopFive(title='Remember', content=','.join(remember_list), user_id=current_user.id,
                                      date=today)
            db.session.add(remember_bullet)
            db.session.commit()
          # Spara ändringarna i databasen
        flash('Listor sparade!', 'success')

    # Hämta listor för att visa på sidan
    priorities = TopFive.query.filter_by(user_id=current_user.id, title="To-Do").first()
    if priorities:
        to_do_list = priorities.content.split(',')
    else:
        to_do_list = []
    to_think_list = TopFive.query.filter_by(user_id=current_user.id, title="Think").first()
    if to_think_list:
        to_think_list = to_think_list.content.split(',')
    else:
        to_think_list = []

    remember_list = TopFive.query.filter_by(user_id=current_user.id, title="Remember").first()
    if remember_list:
        remember_list = remember_list.content.split(',')
    else:
        remember_list = []
    return render_template('cal/myWeek.html', sida='Veckoplanering', week_scores=weekData, header='Veckoplanering',
                           total_score=0, sub_menu=sub_menu, bullet=bullet, timedelta=timedelta,
                           week=week_num, week_dates=week_dates, to_do_list=to_do_list, to_think_list=to_think_list,
                           remember_list=remember_list, current_date=current_date)

@cal_bp.route('/timebox', methods=['GET', 'POST'])
@login_required
def timebox():
    today = datetime.now()
    current_date = today.date()

    sida, sub_menu = common_route('Min Dag', ['/cal/month', '/cal/week', '/cal/timebox'],
                                  ['Min Månad', 'Min Vecka', 'Min Dag'])

    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Hämta aktiviteter (scores) för användaren för den aktuella dagen
    scores = db.session.query(
        Activity.name.label('activity_name'),
        Score.Start,
        Score.End,
        Score.Time,
        Score.Date
    ).join(
        Activity, Activity.id == Score.Activity
    ).filter(
        Score.user_id == current_user.id
    ).filter(
        Score.Date >= start_date.date()
    ).filter(
        Score.Date <= end_date.date()
    ).all()

    if request.method == 'POST':
        # Spara To-Do listan
        if 'save_todo' in request.form:
            todo_list = [request.form.get(f'todo_{i}') for i in range(1, 6) if request.form.get(f'todo_{i}')]
            # Skapa en ny post med titel "To-Do" och spara listan som innehåll
            todo_bullet = TopFive(title='To-Do', content=','.join(todo_list), user_id=current_user.id,
                                  date=today)
            db.session.add(todo_bullet)
            db.session.commit()
        # Spara Think listan
        if 'save_think' in request.form:
            think_list = [request.form.get(f'think_{i}') for i in range(1, 6) if request.form.get(f'think_{i}')]
            think_bullet = TopFive(title='Think', content=','.join(think_list), user_id=current_user.id,
                                   date=today)
            db.session.add(think_bullet)
            db.session.commit()
        # Spara Remember listan
        if 'save_remember' in request.form:
            remember_list = [request.form.get(f'remember_{i}') for i in range(1, 6) if
                             request.form.get(f'remember_{i}')]
            remember_bullet = TopFive(title='Remember', content=','.join(remember_list), user_id=current_user.id,
                                      date=today)
            db.session.add(remember_bullet)
            db.session.commit()
          # Spara ändringarna i databasen
        flash('Listor sparade!', 'success')

    # Hämta listor för att visa på sidan
    priorities = TopFive.query.filter_by(user_id=current_user.id, title="To-Do").first()
    if priorities:
        to_do_list = priorities.content.split(',')
    else:
        to_do_list = []
    to_think_list = TopFive.query.filter_by(user_id=current_user.id, title="Think").first()
    if to_think_list:
        to_think_list = to_think_list.content.split(',')
    else:
        to_think_list = []
    remember_list = TopFive.query.filter_by(user_id=current_user.id, title="Remember").first()
    if remember_list:
        remember_list = remember_list.content.split(',')
    else:
        remember_list = []

    return render_template('cal/timebox.html', current_date=today, sida=sida,today=current_date,
                           header=sida, sub_menu=sub_menu, scores=scores,
                           to_do_list=to_do_list, to_think_list=to_think_list, remember_list=remember_list)

# endregion