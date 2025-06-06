from extensions import db
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, Goals, Friendship, Notes, SharedItem, Tasks, Milestones,Deadline)
from sqlalchemy import and_
from pmg_func import (common_route, create_notification)
from flask_login import current_user, login_required

from classes.scoreHandler import ScoreAnalyzer,UserScores
from classes.textHandler import textHandler
from classes.plotHandler import PlotHandler

scorehand = ScoreAnalyzer()
datahand = PlotHandler()
texthand = textHandler()

goals_bp = Blueprint('goals', __name__, template_folder='templates/pmg')
#Region API
@goals_bp.route('/api/usergoals', methods=['GET'])
@login_required
def getGoals():
    goals = Goals.query.filter_by(user_id=current_user.id).all()
    goal_data = []
    for goal in goals:
        goal_data.append({
        "id": goal.id,
        "name":goal.name,
        })

    return jsonify(goal_data)

#endregion API

#region Goals
@goals_bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    sida, sub_menu = common_route("Mina Mål", ['/streaks/streak', '/goals/goals', '/cal/milestones'],
                                  ['Streaks', 'Goals', 'Milestones'])
    start_activity = request.args.get('start_activity', None)
    mygoals = current_user.user_goals

    if request.method == 'POST':

        if 'addGoal' in request.form['action']:
            goal_name = request.form.get('goalName')
            friend_id = request.form.get('friend_id')
            print(friend_id)

            if friend_id == "none":
                # Skapa ett nytt mål för den inloggade användaren
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
            else:
                # Skapa målet först
                new_goal = Goals(name=goal_name, user_id=current_user.id)
                db.session.add(new_goal)
                db.session.flush()  # Få mål-ID utan att committa

                # Skapa SharedItem-poster för både skaparen och vännen
                shared_goal_user = SharedItem(
                    item_type='goal',
                    item_id=new_goal.id,
                    owner_id=current_user.id,
                    shared_with_id=current_user.id,
                    status='accepted'
                )
                shared_goal_friend = SharedItem(
                    item_type='goal',
                    item_id=new_goal.id,
                    owner_id=current_user.id,
                    shared_with_id=friend_id,
                    status='pending'
                )
                db.session.add_all([shared_goal_user, shared_goal_friend])

                # Skapa en notifikation för vännen
                create_notification(
                    user_id=friend_id,
                    message=f"{current_user.username} has invited you to share the goal: '{goal_name}'.",
                    related_item_id=new_goal.id,
                    item_type='goal'
                )

            db.session.commit()  # Slutför allt i en transaktion
            return redirect(url_for('goals.goals', goal_id=goal_id))
        
        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = Tasks(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            return redirect(url_for('pmg.goals'))

    personal_goals = [goal for goal in mygoals if not SharedItem.query.filter_by(item_id=goal.id, item_type='goal').first()]

    shared_goals = [goal for goal in mygoals if SharedItem.query.filter_by(item_id=goal.id, item_type='goal').first()]

    # Hämta mottagna mål-förfrågningar som ännu inte accepterats
    received_requests = db.session.query(
        SharedItem.id.label('request_id'),  # ID för förfrågan
        Goals.name.label('goal_title'),  # Målets namn
        User.username.label('created_by')  # Skaparen av målet
    ).join(
        Goals, SharedItem.item_id == Goals.id
    ).join(
        User, Goals.user_id == User.id
    ).filter(
        SharedItem.shared_with_id == current_user.id,  # Förfrågningar till den inloggade användaren
        SharedItem.status == 'pending',  # Endast ej accepterade förfrågningar
        SharedItem.item_type == 'goal'  # Endast för mål
    ).all()

    # Hämta skickade mål-förfrågningar som ännu inte accepterats
    sent_requests = db.session.query(
        SharedItem.id.label('request_id'),  # ID för förfrågan
        Goals.name.label('goal_title'),  # Målets namn
        User.username.label('sent_to')  # Mottagaren av förfrågan
    ).join(
        Goals, SharedItem.item_id == Goals.id
    ).join(
        User, SharedItem.shared_with_id == User.id
    ).filter(
        SharedItem.owner_id == current_user.id,  # Förfrågningar från den inloggade användaren
        SharedItem.status == 'pending',  # Endast ej accepterade förfrågningar
        SharedItem.item_type == 'goal'  # Endast för mål
    ).all()

    # Hämta vänner för att kunna dela mål
    accepted_friends = Friendship.query.filter_by(user_id=current_user.id, status='accepted').all() + \
                       Friendship.query.filter_by(friend_id=current_user.id, status='accepted').all()
    
    accepted_user_ids = [friend.user_id if friend.user_id != current_user.id else friend.friend_id for friend in
                         accepted_friends]
    
    friends = User.query.filter(User.id.in_(accepted_user_ids)).all()

    
    return render_template('pmg/goals.html',
                           received_requests=received_requests,
                           sent_requests=sent_requests,
                           sida=sida,
                           header=sida,
                           personal_goals=personal_goals,
                           sub_menu=sub_menu,
                           friends=friends,
                           shared_goals=shared_goals,
                           start_activity=start_activity)

@goals_bp.route('/goal_request/<int:request_id>/<action>', methods=['POST'])
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
    return redirect(url_for('goals.goals'))

@goals_bp.route('/goal/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goals.query.get_or_404(goal_id)

    if goal.user_id != current_user.id:
        flash("Du har inte behörighet att ta bort detta mål.", "danger")
        return redirect(url_for('pmg.goals'))

    try:
        # Radera relaterade aktiviteter och tasks
        for activity in goal.activities:
            # Ta bort relaterade tasks
            Tasks.query.filter_by(activity_id=activity.id).delete()

            # Ta bort relaterade notes
            Notes.query.filter_by(activity_id=activity.id).delete()

            # Ta bort själva aktiviteten
            db.session.delete(activity)

        # Ta bort milstolpar
        for milestone in goal.milestones:
            db.session.delete(milestone)

        # Ta bort delade objekt
        SharedItem.query.filter_by(item_type='goal', item_id=goal.id).delete()

        # Radera själva målet
        db.session.delete(goal)
        db.session.commit()

        flash("Målet har tagits bort.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('goals.goals'))

@goals_bp.route('pmg/goal_requests', methods=['GET'])
@login_required
def goal_requests():
    # Hämta alla mål-förfrågningar där du är mottagare och de inte är bekräftade
    received_requests = SharedItem.query.filter_by(user_id=current_user.id, confirmed=False).all()

    # Hämta alla mål-förfrågningar du har skickat men som inte är bekräftade
    sent_requests = SharedItem.query.filter(SharedItem.created_by == current_user.id, SharedItem.confirmed == False).all()

    return render_template('goal_requests.html', received_requests=received_requests, sent_requests=sent_requests)

@goals_bp.route('/milestone/<int:milestone_id>/delete', methods=['POST'])
@login_required
def delete_milestone(milestone_id):
    milestone = Milestones.query.get_or_404(milestone_id)

    # Kontrollera att användaren har behörighet att ta bort denna milestone
    if milestone.goal.user_id != current_user.id:
        flash("Du har inte behörighet att ta bort denna milestone.", "danger")
        return redirect(url_for('activities.goal_activities', goal_id=milestone.goal_id))

    db.session.delete(milestone)
    db.session.commit()
    flash("Milestone har tagits bort.", "success")
    return redirect(url_for('activities.goal_activities', goal_id=milestone.goal_id))


@goals_bp.route('/deadline/<int:deadline_id>/delete', methods=['POST'])
@login_required
def delete_deadline(deadline_id):
    deadline = Deadline.query.get_or_404(deadline_id)

    # Kontrollera att användaren har behörighet att ta bort denna deadline
    if deadline.goal.user_id != current_user.id:
        flash("Du har inte behörighet att ta bort denna deadline.", "danger")
        return redirect(url_for('activities.goal_activities', goal_id=deadline.goal_id))

    db.session.delete(deadline)
    db.session.commit()
    flash("Deadline har tagits bort.", "success")
    return redirect(url_for('activities.goal_activities', goal_id=deadline.goal_id))
# endregion

@goals_bp.route('/milestone/<int:milestone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_milestone(milestone_id):
    milestone = Milestones.query.get_or_404(milestone_id)

    if milestone.goal.user_id != current_user.id:
        flash("Du har inte behörighet att redigera denna milestone.", "danger")
        return redirect(url_for('activities.goal_activities', goal_id=milestone.goal_id))

    if request.method == 'POST':
        milestone.name = request.form.get('milestone-name')
        milestone.description = request.form.get('milestone-description')
        milestone.estimated_time = request.form.get('milestone-time')
        
        db.session.commit()

        flash("Milestone har uppdaterats.", "success")
        return redirect(url_for('activities.goal_activities', goal_id=milestone.goal_id))

    return render_template('pmg/edit_milestone.html', milestone=milestone)
