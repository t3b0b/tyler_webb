from random import choice
from extensions import db
from flask import Blueprint, abort, render_template, redirect, url_for, request, jsonify, flash
from models import (User, Notes, Goals, Lists, TopFive,
                    Activity, Score, MyWords)

from pmg_func import (common_route,getInfo,add2db)

from datetime import datetime, timedelta, date

from flask_login import current_user, login_required

txt_bp = Blueprint('txt', __name__, template_folder='templates/txt')

from classes.textHandler import textHandler, userText

text = textHandler()

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
    "Relationer": ["Finns det någon du vill ge extra uppmärksamhet till idag?",
                   "Finns det någon du vill ge extra uppmärksamhet till imorgon?"],
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

def sync_blog_titles_to_mywords(user):
    # Hämta alla rubriker från Notes där activity_id är None
    all_titles = db.session.query(Notes.title).filter(Notes.activity_id == None).distinct().all()
    all_titles = [title[0] for title in all_titles]

    # Hämta alla ord från MyWords-tabellen för användaren
    existing_words = db.session.query(MyWords.word).filter_by(user_id=user.id).all()
    existing_words = {word[0] for word in existing_words}  # Gör om till en set för snabbare jämförelse

    # Identifiera saknade rubriker
    missing_titles = [title for title in all_titles if title not in existing_words]

    # Lägg till saknade rubriker i MyWords
    new_words = [MyWords(word=title, user_id=user.id) for title in missing_titles]
    db.session.add_all(new_words)
    db.session.commit()

    print(f"Lade till {len(new_words)} nya rubriker i MyWords.")



#region Journal

@txt_bp.route('/sync_titles', methods=['GET'])
@login_required
def sync_titles():
    sync_blog_titles_to_mywords(current_user)
    flash('Synkronisering av bloggrubriker till MyWords slutförd!', 'success')
    return redirect(url_for('txt.blog'))

@txt_bp.route('/update_post/<int:post_id>', methods=['POST'])
@login_required
def update_post(post_id):
    note = Notes.query.get_or_404(post_id)

    # Kontrollera att användaren äger anteckningen
    if note.user_id != current_user.id:
        return jsonify({'error': 'Inte behörig'}), 403

    data = request.get_json()
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)

    db.session.commit()
    return jsonify({'success': 'Inlägget uppdaterades!'})

#txt_bp.route
@txt_bp.route('/my-words')
def my_words():
    pass

#region TopFive
@txt_bp.route('/update_topfive/<int:topfive_id>', methods=['POST'])
@login_required
def update_topfive(topfive_id):
    topfive = TopFive.query.get_or_404(topfive_id)
    if topfive.user_id != current_user.id:
        abort(403)

    # Hämta fält från formuläret, tillåt tomma fält
    topfive.one = request.form.get('one', '').strip()
    topfive.two = request.form.get('two', '').strip()
    topfive.three = request.form.get('three', '').strip()
    topfive.four = request.form.get('four', '').strip()
    topfive.five = request.form.get('five', '').strip()

    db.session.commit()
    flash("Listan uppdaterades!", "success")
    return redirect(url_for('txt.topfive'))  # Ändra till rätt vy

@txt_bp.route('/topfive', methods=['GET', 'POST'])
@login_required
def topfive():
    texthand = userText(current_user.id)
    question, ordet, list_date = texthand.get_daily_question()
    topFive = TopFive.query.filter_by(user_id=current_user.id,title=ordet).first()
    page_url = 'txt.journal'
    titles = TopFive.query.filter_by(user_id=current_user.id).all()
    sida = "Top Five"
    myGoals = Goals.query.filter_by(name="Skriva", user_id=current_user.id).first()
    if myGoals:
        activities = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
        titles_list = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
        titles = [item.name for item in titles_list]
    if not topFive:
            topFive = TopFive(title=ordet, user_id=current_user.id)
            db.session.add(topFive)
            db.session.commit()

    return render_template('txt/topfive.html', side_options=titles, question=question, 
                           ordet=ordet, topFive=topFive, titles=titles, sida=sida, page_url=page_url)
#endregion
@txt_bp.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    section_name = request.args.get('section_name')
    my_act = Activity.query.filter_by(name=section_name, user_id=current_user.id).all()
    activity_names = [act.name for act in my_act]
    texthand=userText(current_user.id)
    if not section_name:
        return redirect(url_for('txt.journal', section_name='Mina Ord'))

    if section_name == 'Mina Ord' or section_name == 'skriva':
        act_id = texthand.section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Ord", [url_for('txt.journal', section_name='skriva'),
                                                   url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    if section_name == 'Mina Mål':
        act_id = texthand.section_content(Activity, section_name)
        sida, sub_menu = common_route("Mina Mål", [url_for('txt.journal', section_name='skriva'),
                                                   url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu,None)

    elif section_name == "Bullet" or section_name == "Lista":
        return topfive()

    elif section_name in activity_names:
        act_id = texthand.section_content(Activity, section_name)
        sida, sub_menu = common_route(section_name, [url_for('txt.journal', section_name='skriva'),
                                                     url_for('txt.journal', section_name='blogg')], ['Skriv', 'Blogg'])
        return journal_section(act_id, sida, sub_menu, None)

@txt_bp.route('/journal/<section_name>', methods=['GET', 'POST'])
@login_required
def journal_section(act_id, sida, sub_menu, my_posts):
    texthand=userText(current_user.id)
    activity = Activity.query.filter_by(user_id=current_user.id,name=sida).first()
    start_activity = request.args.get('start_activity', None)
    page_info = ""
    current_date = date.today()
    why_G = ""
    page_url = 'txt.journal'
    activities = None
    ordet, ord_lista = texthand.getWord()
    today = datetime.now().date()

    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet,ord_lista = texthand.getWord()

    if sida == 'Dagbok':
        ordet = current_date

    elif sida == 'Mina Mål':
        MyWords.query.filter_by(user_id=current_user.id).all()
        if not MyWords:
            texthand.add_words_from_file('orden.txt')
        goals = Goals.query.filter_by(user_id=current_user.id).with_entities(Goals.name).all()
#        used_goals = WhyGoals.query.filter_by(user_id=current_user.id).with_entities(WhyGoals.goal).all()
        goal_list = [goal[0] for goal in goals]
#        used_goal_list = [used_goal[0] for used_goal in used_goals]
        for goal in goal_list:
#            if not goal in used_goal_list:
            ordet = f'Varför är detta mål viktigt för dig? ({goal})'
#           why_G = goal
            break

    if act_id is not None:
        print(act_id)
        myGoals = Goals.query.filter_by(name="Skriva", user_id=current_user.id).first()
        if myGoals:
            activities = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles_list = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles = [item.name for item in titles_list]

    if request.method == 'POST':
        option = request.form.get('option')
        content_check = request.form.get('blogg-content')
        if content_check:
            if option == "write-on-time":

                goal_id = request.form.get('gID')
                activity_id = request.form.get('aID')
                actDate = today
                start = request.form.get('start')
                end = request.form.get('end')
                score = request.form.get('score')
                
                NewScore = Score(
                    user_id=current_user.id,
                    goal_id=goal_id,
                    activity_id=activity_id,
                    Date=actDate,
                    Start=start,
                    End=end,
                    Time=score
                )
                db.session.add(NewScore)
                db.session.commit()
            if sida == 'Dagbok':
                add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], current_user)
            elif sida == 'Mina Ord':
                nytt_ord = request.form.get('post-ord')
                texthand.add_unique_word(nytt_ord)
                add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], current_user)
            elif sida == 'Bullet':
                print("Bullet section")

    return render_template('txt/journal.html', goal=myGoals, activities=activities, side_options=titles, goal_id =activity.goal_id,
                           ordet=ordet, sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu,
                           current_date=current_date, page_url=page_url, act_id=act_id, myPosts=my_posts,
                           page_info=page_info, why_G=why_G, start_activity=start_activity)

@txt_bp.route('/get-new-word')
def get_new_word(section_id):
    texthand=userText(current_user.id)
    ordet = None
    ordet,ord_lista = texthand.getWord()
    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet, ord_lista = texthand.getWord()

    return jsonify(ordet)


@txt_bp.route('/blog/', defaults={'section_name': None}, methods=['GET', 'POST'])
@txt_bp.route('/blog/<section_name>', methods=['GET', 'POST'])
@login_required
def blog(section_name):
    if section_name:
        my_posts = Notes.query.filter_by(title=section_name, user_id=current_user.id).order_by(Notes.date.desc()).all()
    else:
        my_posts = Notes.query.filter_by(user_id=current_user.id, activity_id=None).order_by(Notes.date.desc()).all()
    sida, sub_menu = common_route("Blog", [
        url_for('txt.journal', section_name='skriva'),
        url_for('txt.blog', section_name=None)
    ], ['Skriv', 'Blogg'])

    titles_list = Notes.query.filter_by(user_id=current_user.id).distinct().with_entities(Notes.title).all()
    titles = [item[0] for item in titles_list]

    page_url = 'txt.blog'

    return render_template('txt/blog.html',
                           page_url=page_url,
                           side_options=titles,
                           myPosts=my_posts,
                           sida=sida,
                           header=sida)


@txt_bp.route('/delete_post/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    note = Notes.query.get_or_404(post_id)

    # Kontrollera att användaren äger anteckningen
    if note.user_id != current_user.id:
        return jsonify({'error': 'Inte behörig'}), 403

    db.session.delete(note)
    db.session.commit()
    return jsonify({'success': 'Inlägget raderades!'})

# endregion