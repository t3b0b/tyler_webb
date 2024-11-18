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

@cal_bp.route('/get_activities/<int:goal_id>', methods=['GET'])
@login_required
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id).all()
    activities_data = [{'id': act.id, 'name': act.name} for act in activities]
    return jsonify(activities_data)


@cal_bp.route('/day/<string:date>', methods=['GET', 'POST'])
@login_required
def day_view(date):
<<<<<<< HEAD
    # Hämta dagens event
=======
    # Konvertera `date` från sträng till datetime-objekt
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        flash("Ogiltigt datumformat. Använd 'YYYY-MM-DD'.", 'danger')
        return redirect(url_for('cal.month_view'))

>>>>>>> 5189c3f766ccdafa68097b3cf94a042c1c6e481f
    events = Event.query.filter_by(user_id=current_user.id, date=date).all()
    goals = Goals.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Hantera POST för att skapa event eller deadline
        event_name = request.form.get('event-name')
<<<<<<< HEAD
        start_time = request.form.get('event-start')
        end_time = request.form.get('event-end')
        location = request.form.get('event-location')
        goal_id = request.form.get('goal-id')  # Kan vara None för vanliga events

        # Validera och skapa en ny händelse
        if event_type and event_name and start_time:
=======
        event_type = request.form.get('eventType')
        start_time = request.form.get('event-start')
        end_time = request.form.get('event-end')
        goal_id = request.form.get('goal-id')

        if event_name and event_type and start_time:
>>>>>>> 5189c3f766ccdafa68097b3cf94a042c1c6e481f
            new_event = Event(
                name=event_name,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
<<<<<<< HEAD
                location=location,
                user_id=current_user.id,
                date=date,
                goal_id=goal_id if event_type == 'deadline' else None  # Koppla mål endast om det är en deadline
            )
            db.session.add(new_event)
            db.session.commit()
            flash(f'{event_type.capitalize()} "{event_name}" added successfully.', 'success')
        else:
            flash('Please provide all required fields.', 'danger')

        return redirect(url_for('pmg.day_view', date=date))

    return render_template('pmg/day.html', date=date, events=events, goals=goals)
=======
                date=date,
                user_id=current_user.id,
                goal_id=goal_id or None
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event added successfully!', 'success')
        else:
            flash('Please provide all required fields.', 'danger')

        return redirect(url_for('cal.day_view', date=date.strftime('%Y-%m-%d')))
>>>>>>> 5189c3f766ccdafa68097b3cf94a042c1c6e481f

    return render_template('cal/day_view.html', date=date, events=events, goals=goals)

@cal_bp.route('/month', methods=['GET', 'POST'])
@cal_bp.route('/month/<int:year>/<int:month>')
@login_required
def month(year=None, month=None):
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
                           sub_menu=sub_menu, month=month, today_date=today_date, dag_data=dag_data)

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