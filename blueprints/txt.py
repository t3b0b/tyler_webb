from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, db, Notes, Goals, Bullet,
                    Activity, Score, MyWords, Settings, Dagar)

from pmg_func import (section_content,common_route,getInfo,
                      getWord, add2db, update_dagar)

from datetime import datetime, timedelta, date

from flask_login import current_user

txt_bp = Blueprint('txt', __name__, template_folder='templates/txt')

#region Journal

@txt_bp.route('/journal', methods=['GET', 'POST'])
def journal():
    section_name = request.args.get('section_name')
    my_act = Activity.query.filter_by(name=section_name, user_id=current_user.id).all()
    activity_names = [act.name for act in my_act]

    if not section_name:
        return redirect(url_for('txt.journal', section_name='Mina Ord'))

    if section_name == 'Mina Ord' or section_name == 'skriva':
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Ord", [url_for('txt.journal', section_name='skriva'),
                                                   url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    if section_name == 'Mina Mål':
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Mål", [url_for('txt.journal', section_name='skriva'),
                                                   url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    elif section_name == "Bullet" or section_name == "Lista":
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route("Bullet", [url_for('txt.journal', section_name='skriva'),
                                                 url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

    elif section_name in activity_names:
        act_id = section_content(Activity, section_name)
        sida, sub_menu = common_route(section_name, [url_for('txt.journal', section_name='skriva'),
                                                     url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

    elif section_name == 'blogg':
        sida, sub_menu = common_route("Blogg", [url_for('txt.journal', section_name='skriva'),
                                                url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = Notes.query.filter_by(user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)

    else:
        sida, sub_menu = common_route(section_name, [url_for('txt.journal', section_name='skriva'),
                                                     url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        my_posts = Notes.query.filter_by(title=section_name, user_id=current_user.id).all()
        return journal_section(None, sida, sub_menu, my_posts)

@txt_bp.route('/journal/<section_name>', methods=['GET', 'POST'])
def journal_section(act_id, sida, sub_menu, my_posts):
    page_info = ""
    current_date = date.today()
    why_G = ""
    page_url = 'txt.journal'
    activities = None
    ordet,ord_lista = getWord()

    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet,ord_lista = getWord()

    if sida == 'Dagbok':
        ordet = current_date
    elif sida == 'Mina Mål':
        goals = Goals.query.filter_by(user_id=current_user.id).with_entities(Goals.name).all()
#        used_goals = WhyGoals.query.filter_by(user_id=current_user.id).with_entities(WhyGoals.goal).all()
        goal_list = [goal[0] for goal in goals]
#        used_goal_list = [used_goal[0] for used_goal in used_goals]
        for goal in goal_list:
#            if not goal in used_goal_list:
            ordet = f'Varför är detta mål viktigt för dig? ({goal})'
#           why_G = goal
            break
    elif sida == "Bullet":
        ordet = ['Tacksam för', 'Inför imorgon', "Personer som betyder",
                 'Distraherar mig', 'Motiverar mig',
                 'Jag borde...', 'Värt att fundera på', 'Jag ska försöka..']

    timeInt = Settings.query.filter_by(user_id=current_user.id).first()
    if timeInt and timeInt.stInterval:
        time = timeInt.stInterval
    else:
        time = 15  # Standardvärde om stInterval saknas eller om ingen inställning hittas

    titles = []  # Initialisera titles här för att säkerställa att den alltid har ett värde

    if act_id is not None:
        print(act_id)
        myGoals = Goals.query.filter_by(name="Skriva", user_id=current_user.id).first()
        if myGoals:
            activities = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles_list = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles = [item.name for item in titles_list]
    elif act_id is None:
        myGoals = None
        activities = None
        titles_list = Notes.query.filter_by(user_id=current_user.id).distinct().with_entities(Notes.title).all()
        titles = [item[0] for item in titles_list]

    if request.method == 'POST':
        option = request.form.get('option')
        print(option)
        user = User.query.filter_by(id=current_user.id).first()
        content_check = request.form['blogg-content']
        if content_check:
            if option == 'timeless':
                if sida == 'Dagbok':
                    add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Mina Ord':

                    nytt_ord = request.form.get('post-ord')
                    new_word=MyWords(word=nytt_ord, user_id=current_user.id)
                    db.session.add(new_word)
                    db.session.commit()

                    add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Bullet':
                    theme = request.form['post-ord']
                    bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'], request.form['#5']]
                    newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list, date=current_date, user_id=current_user.id)
                    db.session.add(newBullet)
                    db.session.commit()
#                elif sida == 'Mina Mål':
#                    add2db(WhyGoals,request,['post-ord','blogg-content','goal'],['title','text','goal'],user)
            elif option == "write-on-time":
                add2db(Score, request, ['gID', 'aID', 'aDate', 'score'], ['Goal', 'Activity', 'Date', 'Time'], user)
                if sida == 'Dagbok':
                    add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Mina Ord':
                    add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Bullet':
                    theme = request.form['post-ord']
                    bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'],
                                   request.form['#5']]
                    newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list,
                                       date=current_date, user_id=current_user.id)
                    db.session.add(newBullet)
                    db.session.commit()

                update_dagar(current_user.id,Dagar)
    return render_template('txt/journal.html', time=time, goal=myGoals, activities=activities, side_options=titles,
                           ordet=ordet, sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu,
                           current_date=current_date, page_url=page_url, act_id=act_id, myPosts=my_posts,
                           page_info=page_info, why_G=why_G)

@txt_bp.route('/get-new-word')
def get_new_word(section_id):
    ordet = None
    ordet,ord_lista = getWord()
    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet, ord_lista = getWord()

    return jsonify(ordet)

# endregion