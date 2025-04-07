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

# region Start
@pmg_bp.route('/myday', methods=['GET', 'POST'])
@login_required
def myday():
    analyzer = UserScores(current_user.id)
    sida, sub_menu = common_route("Min Grind", ['/cal/timebox'], ['My Day'])
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

   # plot_url = create_week_comparison_plot(this_week_scores, last_week_scores)

    goalTime = analyzer.sumGoal(last_week_scores)
    lastWeek = analyzer.sumDays(this_week_scores)
    thisWeek = analyzer.sumDays(last_week_scores)

    actTime = analyzer.sumAct(last_week_scores)


    goal_plot = datahand.create_grouped_bar_plot(
        data_dicts=[thisWeek,lastWeek],
        labels_list=['Denna vecka', 'Förra veckan'], 
        title="Tid per dag", 
        ylabel="Tid (min)")


    # ladda Amount till streaks
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
    
# endregion

@pmg_bp.route('/focus_room/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def focus_room(activity_id):
    activity = Activity.query.get_or_404(activity_id)


    if activity.name == 'Springa':
       print(activity.name)
    
    goalId = activity.goal_id
    currentDate = date.today()
    tasks = get_user_tasks(current_user.id, Activity,activity_id)  # Hämta och sortera tasks
    activityNotes = Notes.query.filter_by(user_id=current_user.id, activity_id=activity_id).all()
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

    return render_template('pmg/focus_room.html',activityNotes=activityNotes, activity=activity, tasks=tasks, currentDate=currentDate,goalId=goalId, activityName=activity.name)
