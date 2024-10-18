from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash

from models import (User, db, Streak, Goals,
                    Activity, Score,
                    Event,TopFive,Dagar)

from datetime import datetime, timedelta

from pmg_func import (get_activities_for_user,getInfo,
                      organize_activities_by_time,process_weekly_scores,
                      common_route, update_dagar,generate_calendar_weeks)

from flask_login import current_user, login_required, login_user, logout_user

cal_bp = Blueprint('cal', __name__, template_folder='templates/cal')

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
    # Här hämtar du relevant information om det specifika datumet
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()

    # Hämta befintliga händelser för datumet (events, deadlines, milestones)
    events = Event.query.filter_by(user_id=current_user.id, date=selected_date).all()

    if request.method == 'POST':
        event_type = request.form.get('eventType')
        event_name = request.form.get('event-name')
        event_start = request.form.get('event-start')
        event_end = request.form.get('event-end')

        # Skapa nytt event, milestone eller deadline beroende på valt alternativ
        new_event = Event(name=event_name, event_type=event_type, start_time=event_start, end_time=event_end,
                          user_id=current_user.id)
        db.session.add(new_event)
        db.session.commit()

        return redirect(url_for('cal.day_view', date=date))

    return render_template('cal/day_view.html', date=selected_date, events=events)


@cal_bp.route('/month', methods=['GET', 'POST'])
@cal_bp.route('/month/<int:year>/<int:month>')
@login_required
def month(year=None, month=None):
    page_info=getInfo('pageInfo.csv', 'myMonth')
    sida, sub_menu = common_route('Min Månad', ['/cal/month', '/cal/week', '/cal/timebox'],
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

    return render_template('cal/month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida,
                           sub_menu=sub_menu, month=month, today_date=today_date, dag_data=dag_data,page_info=page_info)

@cal_bp.route('/week', methods=['GET', 'POST'])
@login_required
def week():
    current_date = datetime.now()
    year, week_num, weekday = current_date.isocalendar()
    start_week = current_date - timedelta(days=current_date.weekday())  # Start of the current week
    end_week = start_week + timedelta(days=6)  # End of the current week
    page_info = getInfo('pageInfo.csv', 'myWeek')
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
    return render_template('cal/myWeek.html', sida='Veckoplanering', week_scores=week_scores, header='Veckoplanering',
                           total_score=0, sub_menu=sub_menu, page_info=page_info, bullet=bullet, timedelta=timedelta,
                           week=week_num, week_dates=week_dates, to_do_list=to_do_list, to_think_list=to_think_list,
                           remember_list=remember_list, current_date=current_date)

@cal_bp.route('/timebox', methods=['GET', 'POST'])
@login_required
def timebox():
    page_info = getInfo('pageInfo.csv', 'myDay')
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
                           to_do_list=to_do_list, to_think_list=to_think_list, remember_list=remember_list,
                           page_info=page_info)

# endregion