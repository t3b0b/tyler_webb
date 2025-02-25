from random import choice
from extensions import mail,db
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, Notes, Goals, Bullet, TopFive,
                    Activity, Score, MyWords, Settings, Dagar)

from pmg_func import (section_content,common_route,getInfo,get_daily_question,
                      getWord, add2db, update_dagar,add_unique_word,add_words_from_file)

from datetime import datetime, timedelta, date

from flask_login import current_user, login_required, login_user, logout_user

txt_bp = Blueprint('txt', __name__, template_folder='templates/txt')

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

@txt_bp.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    section_name = request.args.get('section_name')
    my_act = Activity.query.filter_by(name=section_name, user_id=current_user.id).all()
    activity_names = [act.name for act in my_act]
    topFiveList = []  # Se till att variabeln alltid har ett värde
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


@txt_bp.route('/journal/<section_name>', methods=['GET', 'POST'])
@login_required
def journal_section(act_id, sida, sub_menu, my_posts):
    start_activity = request.args.get('start_activity', None)
    topFiveList=[]
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
        MyWords.query.filter_by(user_id=current_user.id).all()
        if not MyWords:
            add_words_from_file('orden.txt',current_user.id)
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
        ordet, list_type, list_date = get_daily_question()
        
        list_title = list_type.capitalize()

        # Försök att hämta en befintlig lista
        topFive = TopFive.query.filter_by(
            title=list_title, 
            user_id=current_user.id, 
            list_type=list_type, 
            date=list_date
        ).first()

        if topFive and topFive.content:
            topFiveList = topFive.content.split(',')
            show = 0
        else:
            topFiveList=[]
            show = 1
            if not topFive:  # Om det inte finns en befintlig lista, skapa en ny
                topFive = TopFive(
                    title=list_title, 
                    user_id=current_user.id, 
                    list_type=list_type, 
                    date=list_date
                )
                db.session.add(topFive)
                db.session.commit()

        titles = TopFive.query.filter_by(user_id=current_user.id).all()

    if act_id is not None:
        print(act_id)
        myGoals = Goals.query.filter_by(name="Skriva", user_id=current_user.id).first()
        if myGoals:
            activities = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles_list = Activity.query.filter_by(goal_id=myGoals.id,user_id=current_user.id).all()
            titles = [item.name for item in titles_list]

    if request.method == 'POST':
        option = request.form.get('option')
        user = User.query.filter_by(id=current_user.id).first()
        content_check = request.form['blogg-content']
        if content_check:
            if option == 'timeless':
                if sida == 'Dagbok':
                    add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                elif sida == 'Mina Ord':
                    nytt_ord = request.form.get('post-ord')
                    add_unique_word(nytt_ord,current_user.id)
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

    return render_template('txt/journal.html', goal=myGoals, activities=activities, side_options=titles,
                           ordet=ordet, sida=sida, header=sida, orden=ord_lista, sub_menu=sub_menu,
                           current_date=current_date, page_url=page_url, act_id=act_id, myPosts=my_posts,
                           page_info=page_info, why_G=why_G, topFiveList = topFiveList,start_activity=start_activity)

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

# endregion