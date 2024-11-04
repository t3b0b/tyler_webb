from random import choice
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from models import (User, db, Notes, Goals, Bullet,
                    Activity, Score, MyWords, Settings, Dagar)

from pmg_func import (section_content,common_route,getInfo,
                      getWord, add2db, update_dagar)
from flask_login import current_user, login_required
from datetime import datetime, timedelta, date

from flask_login import current_user

txt_bp = Blueprint('txt', __name__, template_folder='templates/txt')

#region Journal

@txt_bp.route('/journal', methods=['GET', 'POST'])
def journal():
    section_name = request.args.get('section_name')


    if not section_name:
        return redirect(url_for('txt.my_words', section_name='Mina Ord'))
    
    elif section_name == "Mina Ord" or section_name == "list":
        act_id = section_content(Activity, section_name)
        sida = "My Words"
        return redirect(url_for('txt.my_words', section_name='Mina Ord'))

    elif section_name == "Bullet" or section_name == "list":
        act_id = section_content(Activity, section_name)
        sida = "Lists"
        return redirect(url_for('txt.list', section_name='Bullet'))
    
    elif section_name == "Blog":
        sida = section_name
        my_posts = Notes.query.filter_by(title=section_name, user_id=current_user.id).all()
        return redirect(url_for('txt.blog', None, sida, sub_menu, my_posts))

@txt_bp.route('/list', methods=['GET', 'POST'])
@login_required
def list():
    current_date = date.today()
    act_id = section_content(Activity, 'bullet')
    sida = "Lists"
    ordet = ['Tacksam för', 'Inför imorgon', "Personer som betyder",
             'Distraherar mig', 'Motiverar mig',
             'Jag borde...', 'Värt att fundera på', 'Jag ska försöka..']

    if request.method == 'POST':

        option = request.form.get('option')
        print(option)
        user = User.query.filter_by(id=current_user.id).first()
        content_check = request.form['blogg-content']

        if content_check:
            if option == 'timeless':
                theme = request.form['post-ord']
                bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'], request.form['#5']]
                newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list, date=current_date, user_id=current_user.id)
                db.session.add(newBullet)
                db.session.commit()

            elif option == "write-on-time":
                theme = request.form['post-ord']
                bullet_list = [request.form['#1'], request.form['#2'], request.form['#3'], request.form['#4'],
                                request.form['#5']]
                newBullet = Bullet(theme=theme, author=f'{user.firstName} {user.lastName}', content=bullet_list,
                                    date=current_date, user_id=current_user.id)
                db.session.add(newBullet)
                db.session.commit()
                add2db(Score, request, ['gID', 'aID', 'aDate', 'score'], ['Goal', 'Activity', 'Date', 'Time'], user)

    return render_template('txt/list.html', sida=sida, header=sida, ordet=ordet)


@txt_bp.route('/my_words', methods=['GET', 'POST'])
@login_required
def my_words():
    titles = []
    act_id = section_content(Activity, 'Mina Ord')
    sida = "My Words"
    
    if ordet is None:
        for ord in ord_lista:
            ord.used = False
        db.session.commit()
        ordet, ord_lista = getWord()

    if request.method == 'POST':
        
        ordet, ord_lista = getWord()
        option = request.form.get('option')
        print(option)
        user = User.query.filter_by(id=current_user.id).first()
        content_check = request.form['blogg-content']

        if content_check:
            if option == 'timeless':
                add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)

        elif option == "write-on-time":
                add2db(Notes, request, ['post-ord', 'blogg-content'], ['title', 'content'], user)
                add2db(Score, request, ['gID', 'aID', 'aDate', 'score'], ['Goal', 'Activity', 'Date', 'Time'], user)
    return render_template('txt/my_words.html', sida=sida, header=sida, sub_menu=sub_menu,
                           ordet=ordet, ord_lista=ord_lista)


@txt_bp.route('/blog', methods=['GET', 'POST'])
@login_required
def blog():
    sida = "Blog"
    titles = []
    my_posts = Notes.query.filter_by(user_id=current_user.id).all()
    titles_list = Notes.query.filter_by(user_id=current_user.id).distinct().with_entities(Notes.title).all()
    titles = [item[0] for item in titles_list]

    return render_template('txt/blog.html', sida=sida, header=sida, side_options=titles, my_posts=my_posts)



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