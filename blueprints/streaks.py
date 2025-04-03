
from extensions import db
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (Streak, Goals, Score)
from datetime import datetime, date
from pmg_func import (common_route, add2db,update_streak_details, filter_mod)

from flask_login import current_user, login_required


from classes.scoreHandler import ScoreAnalyzer

from classes.textHandler import textHandler
from classes.plotHandler import PlotHandler

scorehand = ScoreAnalyzer()
datahand = PlotHandler()
texthand = textHandler()
streaks_bp = Blueprint('streaks', __name__, template_folder='templates/pmg')
#region Streak
@streaks_bp.route('/streak',methods=['GET', 'POST'])
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
    return render_template('pmg/streak.html', sida=sida, header=sida,
                           todayDate=current_date, streaks=myStreaks, sub_menu=sub_menu,
                           goals=myGoals)

"""
@pmg_bp.route('/streak/<int:shared_streak_id>/respond', methods=['POST'])
@login_required
def respond_to_streak_invitation(shared_streak_id):
    shared_streak = SharedStreak.query.get_or_404(shared_streak_id)

    if shared_streak.user_id != current_user.id:
        flash("Du har inte rätt att svara på denna inbjudan.", "danger")
        return redirect(url_for('pmg.streak'))

    action = request.form.get('action')
    if action == 'accept':
        shared_streak.status = 'active'
        create_notification(
            user_id=shared_streak.owner_id,
            message=f"{current_user.username} har accepterat streak-inbjudan!",
            related_item_id=shared_streak.id,
            item_type='streak'
        )
        flash("Du har accepterat inbjudan!", "success")
    elif action == 'decline':
        shared_streak.status = 'declined'
        create_notification(
            user_id=shared_streak.owner_id,
            message=f"{current_user.username} har avböjt streak-inbjudan.",
            related_item_id=shared_streak.id,
            item_type='streak'
        )
        flash("Du har avböjt inbjudan.", "info")

    db.session.commit()
    return redirect(url_for('pmg.streak'))
"""


@streaks_bp.route('/streak/<int:streak_id>/details', methods=['GET'])
def streak_details(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    streakdetail = Streak.query.filter_by(user_id=current_user.id, id = streak_id).first()

    return render_template('pmg/details.html', streak=streak, detail=streakdetail)


@streaks_bp.route('/update_streak/<int:streak_id>/<action>', methods=['POST'])
def update_streak(streak_id, action):
    streak = Streak.query.get_or_404(streak_id)
    today = date.today()
    midnight_today = datetime.combine(today, datetime.min.time())  # Sätter tiden till 00:00:00
    current_date = today.strftime('%Y-%m-%d')

    if action == 'check':
        score, goal_id = update_streak_details(streak, midnight_today)
        flash(f"Score: {score}, Goal ID: {goal_id}")  # Lägg till denna rad för felsökning
        amount = request.form.get("amount")
        # Kontrollera att goal_id och score har giltiga värden
        if score:
            new_score = Score(Goal=goal_id, Activity=None, Time=score, Date=current_date, user_id=current_user.id, Streak=streak_id, Amount=amount)
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
        db.session.commit()
        print("Streak reset")  # Lägg till denna rad för felsökning


    return redirect(url_for('pmg.myday'))


@streaks_bp.route('/delete-streak/<int:streak_id>', methods=['POST'])
def delete_streak(streak_id):
    streak = Streak.query.get_or_404(streak_id)
    if streak.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(streak)
    db.session.commit()
    return jsonify({'success': True})
# endregion
