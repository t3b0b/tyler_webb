from random import choice
from extensions import db
import random
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, Streak, Goals, Friendship, Notes, SharedItem, Notification,
                    Activity, Score, Tasks, TopFive, SubTask)
from datetime import datetime, timedelta, date
from sqlalchemy import and_
from pmg_func import (common_route, add2db, getSwetime,get_user_goals,get_user_tasks,update_streak_details,
                      SortStreaks, filter_mod, create_notification)
import pandas as pd
from pytz import timezone
from flask_login import current_user, login_required
from sqlalchemy.orm import scoped_session

from classes.scoreHandler import ScoreAnalyzer,UserScores
from classes.calHandler import Calendar
from classes.textHandler import textHandler
from classes.plotHandler import PlotHandler

scorehand = ScoreAnalyzer()
datahand = PlotHandler()
texthand = textHandler()

tasks_bp = Blueprint('tasks', __name__, template_folder='templates/pmg')

# region Tasks
@tasks_bp.route('/activity/<int:activity_id>/tasks', methods=['GET'])
def activity_tasks(activity_id):
    userScores = UserScores(current_user.id)
    activity = Activity.query.get_or_404(activity_id)
    totalMin = userScores.get_activity_scores(activity_id)
    totalHours = round(totalMin/60,1)

    print (f'Activity name: {activity.name} Total minutes: {totalMin}')
    print (f'Activity name: {activity.name} Total hours: {totalHours}')

    if activity.goal_id not in [goal.id for goal in get_user_goals(current_user.id)]:
        flash("Du har inte behörighet att visa denna aktivitet.", "danger")
        return redirect(url_for('pmg.myday'))

    todos = get_user_tasks(current_user.id, Activity, activity_id)

    sida = f"{activity.name} ToDos"
    return render_template('pmg/activity_tasks.html', activity=activity, tasks=todos, sida=sida, header=sida, totalHours=totalHours)


@tasks_bp.route('/activity/<int:activity_id>/update_task/<int:task_id>', methods=['GET', 'POST'])
def update_task(activity_id, task_id):
    task = Tasks.query.get_or_404(task_id)


    completed = 'completed' in request.form
    page = request.form.get('page')

    task.completed = completed
    task.date_completed = datetime.now().date()
    db.session.commit()

    # Omdirigera till rätt sida baserat på ursprungssidan
    if page == 'todo':
        return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))
    elif page == 'fokus':
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))

    # Om ingen origin skickas med, omdirigera till standard-sidan
    return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))


@tasks_bp.route('/activity/<int:activity_id>/add_task', methods=['POST'])
def add_task(activity_id):
    # Hämta aktiviteten
    activity = Activity.query.get_or_404(activity_id)

    # Kontrollera om aktiviteten är kopplad till ett SharedItem
    shared_item = SharedItem.query.filter_by(
        id=activity.shared_item_id
    ).first()

    # Hämta data från formuläret
    task_name = request.form.get('task_name')
    is_repeatable = request.form.get('is_repeatable') == 'true'
    total_repeats = request.form.get('total_repeats', type=int)

    # Validera task-namn
    if not task_name:
        flash("Task name is required", "danger")
        return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))

    # Skapa ny task
    new_task = Tasks(
        task=task_name,
        completed=False,
        is_repeatable=is_repeatable,
        total_repeats=total_repeats if is_repeatable else None,
        user_id=current_user.id,
        activity_id=activity.id,
        shared_item_id=shared_item.id if shared_item else None
    )

    db.session.add(new_task)
    db.session.commit()

    if shared_item:
        # Hämta alla användare som delar aktiviteten
        shared_users = SharedItem.query.filter_by(item_id=activity.id, item_type='activity', status='active').all()
        for shared_user in shared_users:
            if shared_user.shared_with_id != current_user.id:
                create_notification(
                    user_id=shared_user.shared_with_id,
                    message=f"{current_user.username} added the task '{task_name}' to '{activity.name}'.",
                    related_item_id=new_task.id,
                    item_type='task'
                )
                
    if 'fokus' in request.form.get('page'):
        flash("Task added successfully", "success")
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))
    elif 'list' in request.form.get('page'):
        flash("Task added successfully", "success")
        return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))


@tasks_bp.route('/activity/<int:activity_id>/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(activity_id, task_id):
    # Hämta tasken
    task = Tasks.query.get_or_404(task_id)

    # Kontrollera om användaren har åtkomst till aktiviteten
    if task.activity_id != activity_id:
        flash("Ogiltig förfrågan: Aktiviteten matchar inte.", "danger")
        return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))

    # Kontrollera om användaren är ägare till tasken eller att aktiviteten är delad
    if not current_user.id == task.user_id:
        flash("Du har inte behörighet att ta bort denna task.", "danger")
        return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task raderades framgångsrikt.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('tasks.activity_tasks', activity_id=activity_id))

# endregion

# region Subtasks
@tasks_bp.route('/task/<int:task_id>/add_subtask', methods=['POST'])
@login_required
def add_subtask(task_id):
    task = Tasks.query.get_or_404(task_id)
    subtask_name = request.form.get('subtask_name')

    if not subtask_name:
        flash("Subtask name is required", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))

    new_subtask = SubTask(name=subtask_name, task_id=task_id)
    db.session.add(new_subtask)

    task.completed = False

    db.session.commit()

    if 'fokus' in request.form.get('page'):
        flash("Subtask added successfully!", "success")
        return redirect(url_for('pmg.focus_room', activity_id=task.activity_id))
    elif 'list' in request.form.get('page'):
        flash("Subtask added successfully!", "success")
        return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))


@tasks_bp.route('/subtask/<int:subtask_id>/update', methods=['POST'])
def update_subtask(subtask_id):
    subtask = SubTask.query.get_or_404(subtask_id)

    subtask.completed = not subtask.completed  # Växla status på subtask
    if subtask.completed:
        subtask.date_completed=datetime.now().date()
    else: 
        subtask.date_completed=datetime.now().date()
    db.session.commit()

    # 🟢 Hämta alla subtasks för denna task
    all_subtasks = SubTask.query.filter_by(task_id=subtask.task_id).all()
    task = Tasks.query.get(subtask.task_id)

    # 🔍 Kontrollera om alla subtasks är avklarade
    if all(sub.completed for sub in all_subtasks):  # Om alla subtasks är klara
        task.completed = True
        task.date_completed = datetime.now().date() 
    else:
        task.completed = False  # Om minst en subtask är ofullständig
        task.date_completed = None

    db.session.commit()  # Spara ändringar till databasen

    # Omdirigera tillbaka till rätt sida
    if 'fokus' in request.form.get('page'):
        return redirect(url_for('pmg.focus_room', activity_id=task.activity_id))
    elif 'list' in request.form.get('page'):
        return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))


@tasks_bp.route('/task/<int:task_id>/subtasks', methods=['GET'])
@login_required
def get_subtasks(task_id):
    task = Tasks.query.get_or_404(task_id)
    subtasks = SubTask.query.filter_by(task_id=task_id).order_by(SubTask.completed.asc()).all()

    return render_template('pmg/subtasks.html', task=task, subtasks=subtasks)

# endregion