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


pmg_bp = Blueprint('pmg', __name__, template_folder='templates/pmg')



Questions = {

    "Prioriteringar": ["Viktigt att prioritera idag",
                   'Viktigt att prioritera imorgon'],
    "Tacksam": ["Vad har du att vara tacksam för?"],
    "Tankar": ["Tankar/insikter värda att påminnas om",
               "Tankar/insikter att ta med till imorgon"],
    "Bättre": ["Vad ska du se till att göra bättre idag?",
               "Vad ska du se till att göra bättre imorgon?"],
    "Känslor": ["Hur känner du dig idag?",
                "Hur känner du inför imorgon?"],
    "Mål": ["Vilka mål vill du nå idag?",
            "Vilka mål vill du nå imorgon?"],
    "Relationer": ["Vem kan du ge extra uppmärksamhet idag?",
                   "Vem kan du ge extra uppmärksamhet imorgon?"],
    "Lärande": ["Vad vill du lära dig eller utforska idag?",
                "Vad vill du lära dig eller utforska imorgon?"],
    "Hälsa": ["Vad kan du göra idag för att ta hand om din hälsa och energi?",
              "Vad kan du göra imorgon för att ta hand om din hälsa och energi?"],
    "Uppskattning": ["Vad eller vem kan du visa uppskattning för idag?",
                     "Vad eller vem kan du visa uppskattning för imorgon?"],
    "Kreativitet": ["Hur kan du uttrycka din kreativitet idag?",
                    "Hur kan du uttrycka din kreativitet imorgon?"],
    "Utmaningar": ["Finns det någon utmaning du kan ta itu med idag?",
                   "Finns det någon utmaning du kan ta itu med imorgon?"],
    "Avslappning": ["Vad kan du göra för att slappna av och återhämta dig idag?",
                    "Vad kan du göra för att slappna av och återhämta dig imorgon?"],
    "Underlätta": ["Vad kan du göra idag för att underlätta morgondagen?",
                    "Vad kan du göra för att underlätta den här dagen?"],
}

@pmg_bp.route('/notifications/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': notification.id,
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications])

@pmg_bp.route('/notifications/mark_as_read', methods=['POST'])
def mark_notifications_as_read():
    try:
        data = request.get_json()  # Kontrollera inkommande JSON
        notification_ids = data.get('notificationIds', [])
        # Validera och uppdatera
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
    start_activity = request.args.get('start_activity', None)

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

        elif 'addTodo' in request.form['action']:
            goal_id = request.form.get('goalId')
            task_content = request.form.get('task')
            if goal_id and task_content:
                new_task = Tasks(task=task_content, goal_id=goal_id, user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
            return redirect(url_for('pmg.goals'))

    # Hämta mål på nytt varje gång sidan laddas för att säkerställa att listan är uppdaterad
    personal_goals = Goals.query.filter(
        Goals.user_id == current_user.id,  # Mål som tillhör nuvarande användare
        ~Goals.id.in_(db.session.query(SharedItem.item_id).filter(
            SharedItem.item_type == 'goal'  # Endast SharedItems kopplade till mål
        ))
    ).all()

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
    shared_item = SharedItem.query.filter_by(item_id=goal_id, item_type='goal', status='active').first()
    start_activity = request.args.get('start_activity', None)

    if request.method == 'POST':
        # Hantera POST-begäran för att lägga till en aktivitet
        goalId = goal_id
        activity_name = request.form.get('activity-name')
        measurement = request.form.get('activity-measurement')

        if activity_name and measurement:
            # Skapa aktivitet
            new_activity = Activity(
                name=activity_name,
                goal_id=goal.id,
                user_id=user,
                shared_item_id=shared_item.id if shared_item else None  # Koppla till delning om målet är delat
            )
            db.session.add(new_activity)
            db.session.commit()

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

            flash('Activity added successfully', 'success')
            return redirect(url_for('pmg.goal_activities', goal_id=goal_id))
        else:
            flash('Activity name and measurement are required', 'danger')

    # Hantera GET-begäran för att visa aktiviteterna
    activities = Activity.query.filter_by(goal_id=goal_id).all()
    return render_template('pmg/activities.html', goal=goal, start_activity=start_activity, activities=activities)

@pmg_bp.route('/goal/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goals.query.get_or_404(goal_id)

    # Kontrollera att användaren äger målet
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

    return redirect(url_for('pmg.goals'))



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
    analyzer = UserScores(current_user.id)

    sida, sub_menu = common_route("Min Grind", ['/pmg/timebox'], ['My Day'])
    now = getSwetime()
    today = now.date()  # Hämta aktuell tid
    yesterday = datetime.now().date() - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    hour = now.hour  # Aktuell timme
    myStreaks = filter_mod(Streak, user_id=current_user.id)
    yesterday_score = analyzer.myDayScore(day_offset=-1)
    total, point_details = analyzer.myDayScore(day_offset=0)
    activity_points = point_details.get("activity_points", 0)
    streak_points = point_details.get("streak_points", 0)

    this_week_scores, activity_scores = analyzer.get_scores_by_period('week',today)
    last_week_scores,lastweek_activity_scores=analyzer.get_scores_by_period('week',today-timedelta(days=7))

    for row in last_week_scores:
        goal = row.goalName or "Okänt mål"
        activity = row.actName or "Okänd aktivitet"
        time = row.Time
        date = row.Date
        print(f"Mål: {goal}, Aktivitet: {activity}, Tid: {time}, Datum: {date}")

   # plot_url = create_week_comparison_plot(this_week_scores, last_week_scores)

    goalTime = analyzer.sumGoal(last_week_scores)
    lastWeek = analyzer.sumDays(this_week_scores)
    thisWeek = analyzer.sumDays(last_week_scores)

    actTime = analyzer.sumAct(last_week_scores)

    for day, total_time in thisWeek.items():
        print(f"Day: {day}, Total tid: {total_time} min")

    for goal, total_time in goalTime.items():
        print(f"Mål: {goal}, Total tid: {total_time} min")

    goal_plot = datahand.create_grouped_bar_plot(
        data_dicts=[thisWeek,lastWeek],
        labels_list=['Denna vecka', 'Förra veckan'], 
        title="Tid per dag", 
        ylabel="Tid (min)")

    for activity, total_time in actTime.items():
        print(f"Activity: {activity}, Total tid: {total_time} min")

    for streak in myStreaks:
                yesterday_score = db.session.query(Score.Amount).filter(
                    Score.Streak == streak.id,
                    Score.Date == yesterday,
                    Score.user_id == streak.user_id
                ).scalar()  # Returnerar endast värdet

                # Lägg till gårdagens score som en attribut
                streak.yesterday_value = int(yesterday_score) if yesterday_score is not None else 0

    # Hämta aktiviteter
    myActs = Activity.query.filter_by(user_id=current_user.id)

    aggregated_scores = {
        "activity_points": activity_points,
        "streak_points": streak_points,
        "total_points": total
    }

    valid_streaks=SortStreaks(myStreaks)

    message, list_type, list_date = texthand.get_daily_question()

    list_title = list_type.capitalize()
    topFive = TopFive.query.filter_by(title=list_title, user_id=current_user.id, list_type=list_type, date=list_date).first()

    if topFive and topFive.content:
        topFiveList = topFive.content.split(',')
        show = 0
    else:
        show = 1
        if not topFive:
            topFive = TopFive(user_id=current_user.id, list_type=list_type, title=list_title, date=list_date)
            db.session.add(topFive)
            db.session.commit()
        topFiveList = []

    # Hantera POST-begäran för att spara prioriteringar
    if 'my_list' in request.form:
        # Hämta användarens inmatningar
        my_list = [request.form.get(f'Prio_{i}') for i in range(1, 6) if request.form.get(f'Prio_{i}')]
        topFive = TopFive.query.filter_by(title=list_title, user_id=current_user.id, list_type=list_type, date=list_date).first()

        if topFive:
            topFive.content = ','.join(my_list)
        else:
            # Skapa en ny post om den inte finns
            topFive = TopFive(title=list_title, content=','.join(my_list), user_id=current_user.id,
                              list_type=list_type, date=list_date)
            db.session.add(topFive)


        # Spara ändringar i databasen
        try:
            db.session.commit()
            flash("Dina prioriteringar har sparats!", "success")
        except Exception as e:
            db.session.rollback()
            print("Fel vid sparning:", str(e))
            flash("Ett fel inträffade vid sparningen.", "danger")


    return render_template('pmg/myday.html', sida=sida, header=sida, current_date=today,
                           acts=myActs, total_score=total, aggregated_scores=aggregated_scores,show=show, my_streaks=valid_streaks,
                           sub_menu=sub_menu, plot_url=goal_plot, message=message, topFiveList=topFiveList,topFive=topFive,title=list_title)


@pmg_bp.route('/myday/<date>')
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

#region Activity

@pmg_bp.route('/update-task-order', methods=['POST'])
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

@pmg_bp.route('/focus_room/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def focus_room(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    goal_id = activity.goal_id  # Hämta goal_id från aktiviteten
    today = date.today()
    current_date = today
    tasks = get_user_tasks(current_user.id, Activity,activity_id)  # Hämta och sortera tasks
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

        task = Tasks.query.get_or_404(task_id)
        task.completed = completed
        db.session.commit()

        return jsonify({"success": True}), 200

    return render_template('pmg/focus_room.html',activity_notes=activity_notes, activity=activity, tasks=tasks, current_date=current_date,goal_id=goal_id)


@pmg_bp.route('/delete-activity/<int:activity_id>', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)

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

    return redirect(url_for('pmg.activities'))


@pmg_bp.route('/get_activities/<goal_id>')
def get_activities(goal_id):
    activities = Activity.query.filter_by(goal_id=goal_id)
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
    # Hämta aktiviteten
    activity = Activity.query.get_or_404(activity_id)

    # Kontrollera om användaren har åtkomst till aktiviteten
    if activity.goal_id not in [goal.id for goal in get_user_goals(current_user.id)]:
        flash("Du har inte behörighet att visa denna aktivitet.", "danger")
        return redirect(url_for('pmg.myday'))  # Omdirigera till en lämplig sida

    # Hämta tasks och subtasks kopplade till aktiviteten
    todos = get_user_tasks(current_user.id, Activity, activity_id)  # Använd den uppdaterade funktionen
    

    sida = f"{activity.name} ToDos"
    return render_template('pmg/activity_tasks.html', activity=activity, tasks=todos, sida=sida, header=sida)

@pmg_bp.route('/activity/<int:activity_id>/update_task/<int:task_id>', methods=['GET','POST'])
def update_task(activity_id, task_id):
    task = Tasks.query.get_or_404(task_id)

    # Hämta den nya statusen från formuläret
    completed = 'completed' in request.form  # Checkbox skickar bara värde om den är markerad
    page = request.form.get('page')  # Hämta ursprungssidan

    # Uppdatera task status
    task.completed = completed
    db.session.commit()

    # Omdirigera till rätt sida baserat på ursprungssidan
    if page == 'todo':
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))
    elif page == 'focus':
        return redirect(url_for('pmg.focus_room', activity_id=activity_id))

    # Om ingen origin skickas med, omdirigera till standard-sidan
    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

@pmg_bp.route('/activity/<int:activity_id>/add_task', methods=['POST'])
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
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

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
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))
    
@pmg_bp.route('/activity/<int:activity_id>/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(activity_id, task_id):
    # Hämta tasken
    task = Tasks.query.get_or_404(task_id)

    # Kontrollera om användaren har åtkomst till aktiviteten
    if task.activity_id != activity_id:
        flash("Ogiltig förfrågan: Aktiviteten matchar inte.", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    # Kontrollera om användaren är ägare till tasken eller att aktiviteten är delad
    if not current_user.id == task.user_id:
        flash("Du har inte behörighet att ta bort denna task.", "danger")
        return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task raderades framgångsrikt.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Något gick fel vid raderingen: {str(e)}", "danger")

    return redirect(url_for('pmg.activity_tasks', activity_id=activity_id))

# endregion

#region Subtasks
@pmg_bp.route('/task/<int:task_id>/add_subtask', methods=['POST'])
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

@pmg_bp.route('/subtask/<int:subtask_id>/update', methods=['POST'])
def update_subtask(subtask_id):
    subtask = SubTask.query.get_or_404(subtask_id)
    subtask.completed = not subtask.completed  # Växla status på subtask
    db.session.commit()

    # 🟢 Hämta alla subtasks för denna task
    all_subtasks = SubTask.query.filter_by(task_id=subtask.task_id).all()
    task = Tasks.query.get(subtask.task_id)

    # 🔍 Kontrollera om alla subtasks är avklarade
    if all(sub.completed for sub in all_subtasks):  # Om alla subtasks är klara
        task.completed = True
    else:
        task.completed = False  # Om minst en subtask är ofullständig

    db.session.commit()  # Spara ändringar till databasen

    # Omdirigera tillbaka till rätt sida
    if 'fokus' in request.form.get('page'):
        return redirect(url_for('pmg.focus_room', activity_id=task.activity_id))
    elif 'list' in request.form.get('page'):
        return redirect(url_for('pmg.activity_tasks', activity_id=task.activity_id))
    
@pmg_bp.route('/task/<int:task_id>/subtasks', methods=['GET'])
@login_required
def get_subtasks(task_id):
    task = Tasks.query.get_or_404(task_id)
    subtasks = SubTask.query.filter_by(task_id=task_id).order_by(SubTask.completed.asc()).all()

    return render_template('pmg/subtasks.html', task=task, subtasks=subtasks)

#endregion