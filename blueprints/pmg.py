from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, db, Streak,Goals,
                    Activity, Score,Dagar,ToDoList)

from datetime import datetime, timedelta, date

from pmg_func import (get_activities_for_user, getWord, getInfo,
                      organize_activities_by_time, parse_date, process_weekly_scores,
                      readWords, common_route, add2db, query, unique,
                      section_content, update_dagar, completed_streaks,
                      update_streak_details, myDayScore, generate_calendar_weeks)
import pandas as pd
from pytz import timezone
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

pmg_bp = Blueprint('pmg', __name__, template_folder='templates/pmg')


#region Streak
@pmg_bp.route('/streak',methods=['GET', 'POST'])
@login_required
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

@pmg_bp.route('/streak/<int:streak_id>/details', methods=['GET'])
def streak_details(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    streakdetail = Streak.query.filter_by(user_id=current_user.id, id = streak_id).first()
    return render_template('pmg/details.html', streak=streak, detail=streakdetail)
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
@pmg_bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    sida, sub_menu = common_route("Mina Mål", ['/pmg/streak', '/pmg/goals', '/pmg/milestones'],
                                  ['Streaks', 'Goals', 'Milestones'])
    if request.method == 'POST':
        if 'addGoal' in request.form['action']:
            add2db(Goals, request, ['goalName'], ['name'], current_user)
            # Omdirigera efter att ha lagt till ett nytt mål för att förhindra dubbla POST-förfrågningar
            return redirect(url_for('pmg.goals'))

        elif 'addActivity' in request.form['action']:
            add2db(Activity, request, ['goalId', 'activity-name', 'activity-measurement'],
                   ['goal_id', 'name', 'measurement'], current_user)
            # Omdirigera efter att ha lagt till en ny aktivitet
            return redirect(url_for('pmg.goals'))

        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = ToDoList(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            # Omdirigera efter att ha lagt till en ny todo-uppgift
            return redirect(url_for('pmg.goals'))

    # Hämta mål på nytt varje gång sidan laddas för att säkerställa att listan är uppdaterad
    my_Goals = query(Goals, 'user_id', current_user.id)

    return render_template('pmg/goals.html', sida=sida, header=sida, goals=my_Goals, sub_menu=sub_menu)

@pmg_bp.route('/goal/<int:goal_id>/activities', methods=['GET', 'POST'])
def goal_activities(goal_id):
    goal = Goals.query.get_or_404(goal_id)
    if request.method == 'POST':
        # Hantera POST-begäran för att lägga till en aktivitet
        userId=current_user.id
        goalId = goal_id
        activity_name = request.form.get('activity-name')
        measurement = request.form.get('activity-measurement')
        if activity_name and measurement:
            new_activity = Activity(name=activity_name, goal_id=goalId, user_id=userId)
            db.session.add(new_activity)
            db.session.commit()
            flash('Activity added successfully', 'success')
            return redirect(url_for('pmg.goal_activities', goal_id=goal_id))
        else:
            flash('Activity name and measurement are required', 'danger')

    # Hantera GET-begäran för att visa aktiviteterna
    activities = Activity.query.filter_by(goal_id=goal_id).all()
    return render_template('pmg/activities.html', goal=goal, activities=activities)

@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id, user_id=current_user.id).all()
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]
    return jsonify(activity_list)

# region Todos
@pmg_bp.route('/activity/<int:activity_id>/tasks', methods=['GET'])
def activity_tasks(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    todos = ToDoList.query.filter_by(activity_id=activity_id, user_id=current_user.id).all()
    sida=f"{activity.name} ToDos"
    return render_template('pmg/activity_tasks.html', activity=activity, tasks=todos, sida=sida, header=sida)

@pmg_bp.route('/activity/<int:activity_id>/add_task', methods=['POST'])
def add_task(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    task_name = request.form.get('task_name')

    sida=f"{activity.name} ToDos"
    if not task_name:
        flash('Task name is required!', 'danger')  # Meddelande vid fel
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    # Skapa ny task
    new_task = ToDoList(task=task_name, completed=False, user_id=current_user.id, activity_id=activity_id)
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))


@pmg_bp.route('/activity/<int:activity_id>/update_task/<int:task_id>', methods=['POST'])
def update_task(activity_id, task_id):
    task = ToDoList.query.get_or_404(task_id)

    # Hämta den nya statusen från formuläret
    completed = 'completed' in request.form  # Checkbox skickar bara värde om den är markerad

    # Uppdatera task status
    task.completed = completed
    db.session.commit()

    # Omdirigera tillbaka till aktivitetsuppgifterna efter uppdateringen
    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id),)
# endregion

@pmg_bp.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    # Här kan du implementera logiken för att ta bort målet från databasen
    goal = Goals.query.get(goal_id)
    if goal:
        db.session.delete(goal)
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': 'Goal not found'}), 404

@pmg_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    activity = Activity.query.get(activity_id)
    if activity:
        db.session.delete(activity)
        db.session.commit()
        return jsonify(success=True), 200
    return jsonify(success=False), 404

#region Milestones
@pmg_bp.route('milestones/<int:goal_id>')
@login_required
def milestones(goal_id):
    return render_template('pmg/milestones.html')

# endregion

@pmg_bp.route('/myday', methods=['GET', 'POST'])
@login_required
def myday():
    pageInfo = getInfo('pageInfo.csv', 'Start')
    sida, sub_menu = common_route("Min Grind", ['/pmg/timebox', '/pmg/streak', '/pmg/goals'],
                                  ['My Day', 'Streaks', 'Goals'])
    date_now = date.today()
    print(date_now)
    update_dagar(current_user.id, Dagar)
    myActs = Activity.query.filter_by(user_id=current_user.id).all()
    # Använd konsekvent my_goals istället för både my_goals och myGoals
    update_dagar(current_user.id, Dagar)
    my_Goals = query(Goals, 'user_id', current_user.id)
    myStreaks = Streak.query.filter(Streak.user_id == current_user.id).all()
    myScore, total = myDayScore(date_now, current_user.id)
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
    valid_streaks = []

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

        elif 'addTodo' in request.form['action']:
            task_name = request.form.get('task_name')
            activity_id = request.form.get('aID')

            new_task = ToDoList(task=task_name, completed=False, user_id=current_user.id, activity_id=activity_id)
            db.session.add(new_task)
            db.session.commit()

    return render_template('pmg/myday.html', sida=sida, header=sida, current_date=date_now, acts=myActs,
                           my_goals=my_Goals, my_streaks=valid_streaks, my_score=myScore, total_score=total,
                           sub_menu=sub_menu, sum_scores=aggregated_scores, page_info=pageInfo, current_goal=current_goal)
@pmg_bp.route('/myday/<date>')
@login_required
def myday_date(date):
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()

    today = datetime.now().date()
    completed_streakNames = completed_streaks(selected_date.strftime('%Y-%m-%d'),Dagar)
    for name in completed_streakNames:
        print(name)
    myGoals = query(Goals, 'user_id', current_user.id)
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





