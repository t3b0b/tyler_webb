from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from models import (User, db, Streak, Goals, Friendship, Notes, SharedItem, ActivityTracking,
                    Activity, Score, Dagar, ToDoList, TopFive)
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta, date
from sqlalchemy import and_
from pmg_func import (getInfo, common_route, add2db, unique,
                      section_content, update_dagar, completed_streaks,
                      update_streak_details, myDayScore,
                      generate_calendar_weeks, filter_mod)
import pandas as pd
from pytz import timezone
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import scoped_session

pmg_bp = Blueprint('pmg', __name__, template_folder='templates/pmg')

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
def get_today_score(user_id):
    """Hämta dagens score för en specifik användare."""
    today = datetime.now().date()
    today_score = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == today
    ).scalar() or 0
    return today_score
def get_yesterday_score(user_id):
    """Hämta gårdagens score för en specifik användare."""
    yesterday = datetime.now().date() - timedelta(days=1)
    yesterday_score = db.session.query(db.func.sum(Score.Time)).filter(
        Score.user_id == user_id,
        db.func.date(Score.Date) == yesterday
    ).scalar() or 0
    return yesterday_score
def get_week_activity_times(user_id):
    """Hämta total tid per aktivitet under aktuell vecka för en specifik användare."""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Måndag i denna vecka
    end_of_week = start_of_week + timedelta(days=6)  # Söndag i denna vecka

    activity_times = db.session.query(
        Activity.name,
        db.func.sum(Score.Time).label('total_time')
    ).join(Score).filter(
        Score.user_id == user_id,
        Score.Date.between(start_of_week, end_of_week)
    ).group_by(Activity.name).all()

    return activity_times
def create_activity_plot(activity_times):
    """Generera en stående stapelgraf med unika färger för varje mål."""
    activity_names = [activity[0] for activity in activity_times]
    total_times = [activity[1] for activity in activity_times]

    # Färger för varje stapel, genereras automatiskt för att vara unika
    colors = plt.cm.get_cmap('tab20', len(activity_names))(range(len(activity_names)))
    plt.figure(figsize=(10, 6),facecolor='none', edgecolor='k',)
    plt.bar(activity_names, total_times, color=colors)  # Stående staplar
    plt.ylabel('Total Tid (min)',fontsize=14)
    plt.xlabel('Aktivitet', fontsize=14)
    plt.xticks(rotation=0, ha='center',fontsize=18)
    plt.yticks(rotation=0, ha='right',fontsize=18)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    # Konvertera bilden till base64 för att inkludera den i HTML
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return plot_url

#region Streak

@pmg_bp.route('/streak',methods=['GET', 'POST'])
@login_required
def streak():
    current_date = date.today()
    current_date = current_date.strftime('%Y-%m-%d')
    sida, sub_menu = common_route("Mina Streaks", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks','Goals','Milestones'])
    myStreaks = filter_mod(Streak,user_id=current_user.id)
    myGoals = filter_mod(Goals, user_id=current_user.id)

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

@pmg_bp.route('/streak/<int:streak_id>/details', methods=['GET'])
def streak_details(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    streakdetail = Streak.query.filter_by(user_id=current_user.id, id = streak_id).first()

    return render_template('pmg/details.html', streak=streak, detail=streakdetail)

@pmg_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = date.today()
    midnight_today = datetime.combine(today, datetime.min.time())  # Sätter tiden till 00:00:00
    current_date = today.strftime('%Y-%m-%d')

    if action == 'check':
        score, goal_id = update_streak_details(streak, midnight_today)
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

@pmg_bp.route('/delete-streak/<int:streak_id>', methods=['POST'])
def delete_streak(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    if streak.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(streak)
    db.session.commit()
    return jsonify({'success': True})
# endregion

#region Goals
@pmg_bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    sida, sub_menu = common_route("Mina Mål", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'],
                                  ['Streaks', 'Goals', 'Milestones'])
    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            goal_name = request.form.get('goalName')
            friend_id = request.form.get('friend_id')
            print(friend_id)

            if friend_id == "none":
                # Skapa ett nytt mål för den inloggade användaren
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
                db.session.commit()
            else:
                # Skapa SharedItem-poster för den inloggade användaren och vännen
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
                db.session.commit()  # Spara mål först för att få id

                # Skapa SharedItem-poster för både skaparen och vännen
                shared_goal_user = SharedItem(item_type='goal', item_id=new_goal.id,
                                              owner_id=current_user.id, shared_with_id=current_user.id,
                                              status='accepted')
                shared_goal_friend = SharedItem(item_type='goal', item_id=new_goal.id,
                                                owner_id=current_user.id, shared_with_id=friend_id, status='pending')
                db.session.add_all([shared_goal_user, shared_goal_friend])
                db.session.commit()

        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = ToDoList(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            return redirect(url_for('pmg.goals'))

    # Hämta mål på nytt varje gång sidan laddas för att säkerställa att listan är uppdaterad
    personal_goals = Goals.query.filter_by(user_id=current_user.id)

    # Hämta alla mål som antingen skapats av användaren eller som användaren har blivit inbjuden till och accepterat
    shared_goals = db.session.query(Goals).select_from(Goals).join(
        SharedItem,
        and_(
            SharedItem.item_id == Goals.id,  # Kopplar mål med SharedItem baserat på item_id
            SharedItem.item_type == 'goal'  # Ser till att det är mål som delas
        )
    ).filter(
        (Goals.user_id == current_user.id) |  # Mål skapade av användaren
        ((SharedItem.shared_with_id == current_user.id) & (SharedItem.status == 'accepted'))  # Accepterade inbjudningar
    ).all()

    # Hämta mottagna mål-förfrågningar som ännu inte accepterats
    received_requests = db.session.query(SharedItem).filter(
        (SharedItem.shared_with_id == current_user.id) &  # Förfrågningar till användaren
        (SharedItem.status == 'pending') &  # Ej accepterade förfrågningar
        (SharedItem.item_type == 'goal')  # Endast för mål
    ).all()

    # Hämta skickade mål-förfrågningar som ännu inte accepterats
    sent_requests = db.session.query(SharedItem).filter(
        (SharedItem.owner_id == current_user.id) &  # Förfrågningar från den inloggade användaren
        (SharedItem.status == 'pending') &  # Ej accepterade förfrågningar
        (SharedItem.item_type == 'goal')  # Endast för mål
    ).all()

    # Hämta vänner för att kunna dela mål
    accepted_friends = Friendship.query.filter_by(user_id=current_user.id, status='accepted').all() + \
                       Friendship.query.filter_by(friend_id=current_user.id, status='accepted').all()
    accepted_user_ids = [friend.user_id if friend.user_id != current_user.id else friend.friend_id for friend in
                         accepted_friends]
    friends = User.query.filter(User.id.in_(accepted_user_ids)).all()

    return render_template('pmg/goals.html', received_requests=received_requests, sent_requests=sent_requests,
                           sida=sida, header=sida, personal_goals=personal_goals, sub_menu=sub_menu,
                           friends=friends, shared_goals=shared_goals)


@pmg_bp.route('/goal_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def handle_goal_request(request_id, action):
    # Hämta SharedItem med ID och säkerställ att det är av typen "goal"
    shared_item = SharedItem.query.get_or_404(request_id)

    # Verifiera att det delade objektet är ett mål
    if shared_item.item_type != 'goal':
        flash("Ogiltig förfrågan: Objektet är inte ett mål.", 'danger')
        return redirect(url_for('pmg.goals'))

    # Kontrollera att användaren har behörighet att hantera förfrågan
    if shared_item.shared_with_id != current_user.id:
        flash("Du har inte behörighet att hantera denna förfrågan.", 'danger')
        return redirect(url_for('pmg.goals'))

    # Hantera olika åtgärder
    if action == 'accept':
        shared_item.status = 'accepted'
        flash("Målet har accepterats!", 'success')
    elif action == 'decline':
        db.session.delete(shared_item)
        flash("Mål-förfrågan har avböjts.", 'info')

    # Spara ändringarna
    db.session.commit()
    return redirect(url_for('pmg.goals'))

@pmg_bp.route('/goal/<int:goal_id>/activities', methods=['GET', 'POST'])
def goal_activities(goal_id):
    goal = Goals.query.get_or_404(goal_id)
    user = current_user.id

    if request.method == 'POST':
        # Hantera POST-begäran för att lägga till en aktivitet
        goalId = goal_id
        activity_name = request.form.get('activity-name')
        measurement = request.form.get('activity-measurement')
        if activity_name and measurement:
            new_activity = Activity(name=activity_name, goal_id=goalId, user_id=user)
            db.session.add(new_activity)
            db.session.commit()
            flash('Activity added successfully', 'success')
            return redirect(url_for('pmg.goal_activities', goal_id=goal_id))
        else:
            flash('Activity name and measurement are required', 'danger')

    # Hantera GET-begäran för att visa aktiviteterna
    activities = Activity.query.filter_by(goal_id=goal_id).all()
    return render_template('pmg/activities.html', goal=goal, activities=activities)

@pmg_bp.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    # Här kan du implementera logiken för att ta bort målet från databasen
    session = scoped_session(db.session)
    with session.begin():
        goal = Goals.query.get(goal_id)
        if goal:
            try:
                db.session.delete(goal)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404

@pmg_bp.route('pmg/goal_requests', methods=['GET'])
@login_required
def goal_requests():
    # Hämta alla mål-förfrågningar där du är mottagare och de inte är bekräftade
    received_requests = SharedItem.query.filter_by(user_id=current_user.id, confirmed=False).all()

    # Hämta alla mål-förfrågningar du har skickat men som inte är bekräftade
    sent_requests = SharedItem.query.filter(SharedItem.created_by == current_user.id, SharedItem.confirmed == False).all()

    return render_template('goal_requests.html', received_requests=received_requests, sent_requests=sent_requests)

# endregion

#region Milestones
@pmg_bp.route('milestones/<int:goal_id>')
@login_required
def milestones(goal_id):
    return render_template('pmg/milestones.html')

# endregion

# region Start
@pmg_bp.route('/myday', methods=['GET', 'POST'])
@login_required
def myday():
    sida, sub_menu = common_route("Min Grind", ['/pmg/timebox', '/pmg/streak', '/pmg/goals'],
                                  ['My Day', 'Streaks', 'Goals'])
    date_now = date.today()
    # Använd konsekvent my_goals istället för både my_goals och myGoals
    myActs = filter_mod(Activity, user_id=current_user.id)
    my_Goals = filter_mod(Goals, user_id=current_user.id)
    myStreaks = filter_mod(Streak, user_id=current_user.id)
    myScore, total = myDayScore(date_now, current_user.id)
    today_score = get_today_score(current_user.id)
    yesterday_score = get_yesterday_score(current_user.id)
    act_times = get_week_activity_times(current_user.id)
    plot_url = create_activity_plot(act_times)
    print(total)
    aggregated_scores = {}
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
    inactiveStreaks = []
    activeStreaks = []

    goal_id = request.args.get('goalSel')  # Om du skickar goal_id som en parameter
    if goal_id:
        current_goal = Goals.query.get('goalSel')
    else:
        current_goal = None

    for streak in myStreaks:
        interval_days = timedelta(days=streak.interval, hours=23, minutes=59, seconds=59)
        if streak.lastReg:
            try:
                last_reg_date = streak.lastReg
                streak_interval = last_reg_date + interval_days

                if last_reg_date.date() == today.date():
                    activeStreaks.append(streak)
                    continue

                if streak.count == 0:
                    inactiveStreaks.append(streak)
                elif streak.count >= 1:
                    if today.date() == streak_interval.date():
                        inactiveStreaks.append(streak)
                    elif streak_interval.date() < today.date():
                        continue
                elif streak_interval.date() < today.date():
                    streak.active = False
                    streak.count = 0
                    db.session.commit()
            except (ValueError, TypeError) as e:
                print(f'Hantera ogiltigt datum: {e}, streak ID: {streak.id}, lastReg: {streak.lastReg}')
        else:
            inactiveStreaks.append(streak)
    if myScore:
        sorted_myScore = sorted([score for score in myScore if score[0] is not None], key=lambda score: score[0])

    if request.method == 'POST':
        if 'save-score' in request.form['action']:
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

    elif 'save_todo' in request.form:
        todo_list = [request.form.get(f'todo_{i}') for i in range(1, 6) if request.form.get(f'todo_{i}')]
        # Skapa en ny post med titel "To-Do" och spara listan som innehåll
        todo_bullet = TopFive(title='To-Do', content=','.join(todo_list), user_id=current_user.id,
                              date=today)
        db.session.add(todo_bullet)
        db.session.commit()
    # Spara Think listan
    elif 'save_think' in request.form:
        think_list = [request.form.get(f'think_{i}') for i in range(1, 6) if request.form.get(f'think_{i}')]
        think_bullet = TopFive(title='Think', content=','.join(think_list), user_id=current_user.id,
                               date=today)
        db.session.add(think_bullet)
        db.session.commit()
    # Spara Remember listan
    elif 'save_remember' in request.form:
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

    return render_template('pmg/myday.html', sida=sida, header=sida, current_date=date_now, acts=myActs,
                           my_goals=my_Goals,activeStreaks=activeStreaks, inactiveStreaks=inactiveStreaks, my_score=myScore, total_score=total, plot_url=plot_url,
                           sub_menu=sub_menu, sum_scores=aggregated_scores, current_goal=current_goal,
                           remember_list=remember_list,to_think_list=to_think_list,to_do_list=to_do_list)
@pmg_bp.route('/myday/<date>')
@login_required
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    session = scoped_session(db.session)
    today = datetime.now().date()
    completed_streakNames = completed_streaks(selected_date.strftime('%Y-%m-%d'),Dagar)
    for name in completed_streakNames:
        print(name)
    with session.begin():
        myGoals = filter_mod(Goals, user_id = current_user.id)
        myStreaks = Streak.query.filter(Streak.user_id == current_user.id, Streak.lastReg != today).all()
        myScore, total = myDayScore(selected_date, current_user.id)

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

#region Activity
@pmg_bp.route('/focus_room/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def focus_room(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    goal_id = activity.goal_id  # Hämta goal_id från aktiviteten
    today = date.today()
    current_date=today
    tasks = ToDoList.query.filter_by(activity_id=activity_id, user_id=current_user.id).order_by(ToDoList.completed.desc()).all()
    activity_notes = Notes.query.filter_by(user_id=current_user.id, activity_id=activity_id).all()
    if request.method == 'POST':
        if 'save-score' in request.form['action']:
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

    if request.method == 'POST':
        task_id = request.json.get('taskId')
        completed = request.json.get('completed')

        task = ToDoList.query.get_or_404(task_id)
        task.completed = completed
        db.session.commit()

        return jsonify({"success": True}), 200

    return render_template('pmg/focus_room.html',activity_notes=activity_notes, activity=activity, tasks=tasks, current_date=current_date)

@pmg_bp.route('/activity/<int:activity_id>/update_task/<int:task_id>', methods=['POST'])
def update_task(activity_id, task_id):
    task = ToDoList.query.get_or_404(task_id)

    # Hämta den nya statusen från formuläret
    completed = 'completed' in request.form  # Checkbox skickar bara värde om den är markerad
    origin = request.form.get('origin')  # Hämta ursprungssidan

    # Uppdatera task status
    task.completed = completed
    db.session.commit()

    # Omdirigera till rätt sida baserat på ursprungssidan
    if origin == 'todo':
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))
    elif origin == 'focus':
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))

    # Om ingen origin skickas med, omdirigera till standard-sidan
    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

@pmg_bp.route('/delete-activity/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    activity = Activity.query.get(activity_id)
    if activity:
        try:
            db.session.delete(activity)
            db.session.commit()
            return "Success", 200  # Returnera en enkel sträng istället för JSON
        except Exception as e:
            db.session.rollback()
            return "Internal server error", 500
    return "Activity not found", 404


@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]
    return jsonify(activity_list)

@pmg_bp.route('/update_note/<int:note_id>', methods=['POST'])
@login_required
def update_note(note_id):
    note = Notes.query.get_or_404(note_id)

    # Kontrollera om användaren äger anteckningen
    if note.user_id != current_user.id:
        flash('You are not authorized to edit this note.', 'danger')
        return redirect(url_for('pmg.goals'))  # Omdirigera om användaren inte äger anteckningen

    # Uppdatera innehållet från formuläret
    note.content = request.form.get('content')

    db.session.commit()
    flash('Note updated successfully!', 'success')

    return redirect(url_for('pmg.myday'))  # Omdirigera till lämplig sida efter uppdatering

@pmg_bp.route('/create_notebook/<int:activity_id>', methods=['POST'])
@login_required
def create_notebook(activity_id):
    title = request.form.get('title')
    description = request.form.get('description')
    user = User.query.filter_by(id=current_user.id).first()

    new_note = Notes(
        title=title,
        content=description or '',
        user_id=current_user.id,
        author=user.username,
        activity_id=activity_id,
        date=datetime.now().strftime('%Y-%m-%d')
    )
    db.session.add(new_note)
    db.session.commit()

    flash('Notebook created successfully!', 'success')
    return redirect(url_for('pmg.focus_room',activity_id=activity_id))  # Omdirigera till mål-sidan eller var du vill

# endregion

# region Todos
@pmg_bp.route('/activity/<int:activity_id>/tasks', methods=['GET'])
def activity_tasks(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    todos = ToDoList.query.filter_by(activity_id=activity_id, user_id=current_user.id).order_by(ToDoList.completed.desc()).all()
    sida=f"{activity.name} ToDos"
    return render_template('pmg/activity_tasks.html', activity=activity, tasks=todos, sida=sida, header=sida)

@pmg_bp.route('/activity/<int:activity_id>/add_task', methods=['POST','GET'])
def add_task(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    task_name = request.form.get('task_name')
    origin = request.form.get('origin')

    sida="PMG"

    new_task = ToDoList(task=task_name, completed=False, user_id=current_user.id, activity_id=activity.id)
    db.session.add(new_task)
    db.session.commit()

    if origin == 'todo':
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))
    elif origin == 'focus':
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))

    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id),sida=sida, header=sida)

# endregion



