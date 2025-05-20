from random import choice
from extensions import db

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, Streak, Goals, Friendship, Notes, SharedItem, Notification,
                    Activity, Score, Tasks, TopFive, SubTask, Deadline, Milestones)
from datetime import datetime, timedelta, date

from pmg_func import (common_route, add2db, getSwetime, get_user_goals, get_user_tasks, update_streak_details,
                      SortStreaks, filter_mod, create_notification)
from flask_login import current_user, login_required

from classes.scoreHandler import ScoreAnalyzer, UserScores
from classes.calHandler import Calendar
from classes.textHandler import textHandler
from classes.plotHandler import PlotHandler

scorehand = ScoreAnalyzer()
datahand = PlotHandler()
texthand = textHandler()

activities_bp = Blueprint('activities', __name__, template_folder='templates/pmg')


@activities_bp.route('/goal/<int:goal_id>/activities', methods=['GET', 'POST'])
def goal_activities(goal_id):
    goal = Goals.query.get_or_404(goal_id)
    milestones = goal.milestones
    userScores = UserScores(current_user.id)
    totalMin = userScores.get_goal_scores(goal_id)

    totalHours = round(totalMin/60,1)
    print (f'Goal name: {goal.name} Total minutes: {totalMin}')
    print (f'Goal name: {goal.name} Total hours: {totalHours}')

    goal_scores=userScores.get_all_goal_scores()
    
    deadlines = goal.deadlines
    shared_item = SharedItem.query.filter_by(item_id=goal_id, item_type='goal', status='active').first()
    start_activity = request.args.get('start_activity', None)


    if request.method == 'POST':
        action = request.form.get('action', None)
        # Hantera POST-begäran för att lägga till en aktivitet
        if action == 'addActivity':
            goalId = goal_id
            activity_name = request.form.get('activity-name')
            measurement = request.form.get('activity-measurement')

            if activity_name and measurement:
                # Skapa aktivitet
                new_activity = Activity(
                    name=activity_name,
                    goal_id=goal.id,
                    user_id=current_user.id,
                    shared_item_id=shared_item.id if shared_item else None  # Koppla till delning om målet är delat
                )
                db.session.add(new_activity)

                if shared_item:
                    # Hämta alla användare som målet är delat med
                    shared_users = SharedItem.query.filter_by(item_id=goal_id, item_type='goal', status='active').all()
                    for shared_user in shared_users:
                        if shared_user.shared_with_id != current_user.id:  # Hoppa över nuvarande användare
                            create_notification(
                                user_id=shared_user.shared_with_id,  # Mottagarens ID
                                message=f"{current_user.username} created a new activity '{activity_name}' in goal '{goal.name}'.",
                                related_item_id=new_activity.id,
                                item_type='activity'
                            )
                db.session.commit()
                flash('Activity added successfully', 'success')
                return redirect(url_for('activities.goal_activities', goal_id=goal_id))
            else:
                flash('Activity name and measurement are required', 'danger')
            return redirect(url_for('activities.goal_activities', goal_id=goal_id))
            
        elif action == "addMilestone":
            
            milestone_name = request.form.get('milestone-name')
            milestone_description = request.form.get('milestone-description')
            milestone_est_time = request.form.get('milestone-time')
            
            new_milestone = Milestones(
                name=milestone_name,
                description=milestone_description,
                estimated_time=milestone_est_time,
                date=datetime.now(),
                user_id=current_user.id,
                goal_id=goal_id)
            db.session.add(new_milestone)
            db.session.commit()
            return redirect(url_for('activities.goal_activities', goal_id=goal_id))
        
        elif action == "addDeadline":
            deadline_name = request.form.get('deadline-name')
            deadline_description = request.form.get('deadline-description')
            deadline_due_date = request.form.get('deadline-date')
            deadline_est_time = request.form.get('deadline-est-time')
            new_deadline = Deadline(
                name=deadline_name,
                description=deadline_description,
                due_date=deadline_due_date,
                user_id=current_user.id,
                goal_id=goal_id)
            db.session.add(new_deadline)
            db.session.commit()
            return redirect(url_for('activities.goal_activities', goal_id=goal_id))

    activities = goal.activities
    
    return render_template('pmg/activities.html', goal=goal, start_activity=start_activity, 
                           activities=activities, deadlines=deadlines, milestones=milestones,
                           totalHours=totalHours)


# region Activity

@activities_bp.route('/update-task-order', methods=['POST'])
@login_required
def update_task_order():
    data = request.get_json()

    # Uppdatera ordningen för varje task och subtask
    for task_data in data:
        task_id = int(task_data['id'])
        task = Tasks.query.get(task_id)
        if task:
            task.order = task_data['order']
            db.session.add(task)

        for subtask_data in task_data['subtasks']:
            subtask_id = int(subtask_data['id'])
            subtask = SubTask.query.get(subtask_id)
            if subtask:
                subtask.order = subtask_data['order']
                db.session.add(subtask)

    db.session.commit()
    return jsonify({'success': True})



@activities_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    goal_id = activity.goal_id

    try:
        # Ta bort relaterade tasks
        Tasks.query.filter_by(activity_id=activity.id).delete()

        # Ta bort relaterade notes
        Notes.query.filter_by(activity_id=activity.id).delete()

        # Ta bort själva aktiviteten
        db.session.delete(activity)
        db.session.commit()

        flash("Aktiviteten har tagits bort.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return goal_activities(goal_id=goal_id)


@activities_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id)
    activity_list = [{'id': activity.id, 'name': activity.name} for activity in activities]

    return jsonify(activity_list)


@activities_bp.route('/update_note/<int:note_id>', methods=['POST'])
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


@activities_bp.route('/create_notebook/<int:activity_id>', methods=['POST'])
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
    return redirect(url_for('pmg.focus_room', activity_id=activity_id))  # Omdirigera till mål-sidan eller var du vill


# endregion



