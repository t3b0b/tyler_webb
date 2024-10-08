from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash

from models import (User, db, Streak, Goals,
                    Activity, Score, Dagar,
                    Idag,Event,CalendarBullet,ViewType)

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
    calendar_bullet = CalendarBullet.query.filter_by(user_id=current_user.id, date=date).first()

    # Om det inte finns någon bullet för det datumet, skapa en ny
    if not calendar_bullet:
        calendar_bullet = CalendarBullet(user_id=current_user.id, date=date)

    # Hämta data från formuläret
    calendar_bullet.to_do = request.form.get('to_do')
    calendar_bullet.to_think = request.form.get('to_think')
    calendar_bullet.remember = request.form.get('remember')

    # Ställ in view_type från URL-parametern
    calendar_bullet.view_type = ViewType[view_type]

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
def week():
    current_date = datetime.now()
    year, week_num, weekday = current_date.isocalendar()
    month = current_date.month
    date = current_date.date()


    page_info = getInfo('pageInfo.csv', 'myWeek')
    date_now = datetime.now()
    user_id = current_user.id
    sida, sub_menu = common_route('Min Vecka', ['/cal/month', '/cal/week', '/cal/timebox'],
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

    bullet = CalendarBullet.query.filter_by(user_id=current_user.id, week_num=week_num,view_type="myWeek").first()

    # Om det inte finns något, skapa ett nytt objekt
    if not bullet:
        bullet = CalendarBullet(user_id=current_user.id, week_num=week_num, view_type="myWeek")
        db.session.add(bullet)

    # Om POST-förfrågan skickas, uppdatera listorna
    if request.method == 'POST':
        if 'save_todo' in request.form:
            todo_list = [request.form.get(f'todo_{i}') for i in range(1, 6) if request.form.get(f'todo_{i}')]
            bullet.to_do = ','.join(todo_list)

        if 'save_think' in request.form:
            think_list = [request.form.get(f'think_{i}') for i in range(1, 6) if request.form.get(f'think_{i}')]
            bullet.to_think = ','.join(think_list)

        if 'save_remember' in request.form:
            remember_list = [request.form.get(f'remember_{i}') for i in range(1, 6) if request.form.get(f'remember_{i}')]
            bullet.remember = ','.join(remember_list)

        db.session.commit()  # Spara ändringarna i databasen
        flash('Listor sparade!', 'success')

    # Hämta listor för att visa på sidan
    to_do_list = bullet.to_do.split(',') if bullet.to_do else []
    to_think_list = bullet.to_think.split(',') if bullet.to_think else []
    remember_list = bullet.remember.split(',') if bullet.remember else []

    return render_template('cal/myWeek.html', sida='Veckoplanering', weekly_data=weekly_data, header='Veckoplanering',
                           total_score=0, sub_menu=sub_menu, activities=activities_dict,page_info=page_info, bullet=bullet, to_do_list=to_do_list, to_think_list=to_think_list, remember_list=remember_list, date=current_date)

@cal_bp.route('/timebox', methods=['GET', 'POST'])
@login_required
def timebox():
    page_info = getInfo('pageInfo.csv', 'myDay')
    current_date = datetime.now().strftime("%Y-%m-%d")
    today = datetime.now()
    viktigt = Idag.query.filter_by(date=today, user_id=current_user.id).all()
    tankar = Idag.query.filter_by(date=today, user_id=current_user.id).all()

    sida, sub_menu = common_route('Min Dag', ['/cal/month', '/cal/week', '/cal/timebox'],
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

        return redirect(url_for('cal.timebox'))

    # Hämta sparade punkter
    saved_entry = Idag.query.filter_by(date=current_date, user_id=current_user.id).first()
    if saved_entry:
        viktigt_saved = saved_entry.viktigt.split(",") if saved_entry.viktigt else []
        tankar_saved = saved_entry.tankar.split(",") if saved_entry.tankar else []
    else:
        viktigt_saved = [""] * 5
        tankar_saved = [""] * 5
    return render_template('cal/timebox.html', current_date=current_date, sida=sida,
                           header=sida, sub_menu=sub_menu, activities=activities_dict,
                           page_info=page_info, viktigt_saved=viktigt_saved, tankar_saved=tankar_saved)

# endregion