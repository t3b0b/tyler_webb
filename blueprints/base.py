from random import choice
from extensions import mail,db
from flask_mail import Mail, Message
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from models import (User, Streak, Notes, Goals, Mail,
                    Activity, Score, MyWords, Settings, Dagar)
from datetime import datetime, timedelta,date
from flask_login import current_user
import pandas as pd
import os

file_path = "texts/tjänster.csv"
df = pd.read_csv(file_path)

base_bp = Blueprint('base', __name__, template_folder='templates/base')
test=[]
df = pd.read_csv(file_path)
data=df.loc[df['Tjänst']=="Mekanik"]

@base_bp.route('/home')
def home_base():
    sida = "Hem"
    info = read_info("texts/unikOrg.txt")
    unik = info.split("*")
    content_header = [unik[i] for i in range(len(unik)) if i % 2 == 0]
    content_text = [unik[i] for i in range(len(unik)) if i % 2 != 0]
    start_info = zip(content_header, content_text)
    return render_template('base/home.html', sida=sida, header="Tyler O'Brien", sideOptions=None, start_info=start_info)



@base_bp.route('/om-oss')
def omOss():
    sida = 'Om oss'
    vision = read_info("texts/om_oss.txt")
    vision = vision.split("*")
    om_header = [vision[i] for i in range(len(vision)) if i % 2 == 0]
    om_text = [vision[i] for i in range(len(vision)) if i % 2 != 0]
    print(om_text)
    om_content = zip(om_header,om_text)
    return render_template('base/om.html', om_content=om_content, sida=sida, header=sida)

#region Tjänster
def get_services_for_section(section_name,data):
    section_name = section_name.title()
    section_header = []
    section_text = []

    data = data.loc[data['Tjänst'] == section_name]

    for row in data['Rubrik']:
        section_header.append(row)
    for row in data['Text']:
        section_text.append(row)

    if section_name == "Mekanik":
        image_name = "static/images/Guld_Kugg.jpeg"

    elif section_name == "Webbutveckling":
        image_name = 'static/images/browsers.png'

    elif section_name == "Automatisering":
        image_name = 'static/images/Code.jpg'

    elif section_name == "Kvalitetsledning":
        image_name = 'static/images/Track.jpg'

    return section_text,section_header,image_name

@base_bp.route('/tjanster')
def tjanster():
    sida = 'Tjänster'
    section_name = request.args.get('section_name')
    if section_name:
        sect_header, sect_text, image_filename = get_services_for_section(section_name, df)
        tjanst_content = zip(sect_header, sect_text)
    else:
        image_filename = ''
        tjanst_content = ['']

    return render_template('base/tjanster.html', contents=tjanst_content,
                           image_filename = image_filename, sida=sida, header=sida)
@base_bp.route('/tjanster/<section_name>')
def service_content(section_name):
    sida = 'Tjänster'
    if section_name:
        sida = section_name
        sect_header, sect_text, image_filename = get_services_for_section(section_name,df)
        tjanst_content = zip(sect_header,sect_text)
        return redirect('base.tjanster', contents=tjanst_content, image_filename=image_filename,
                        sida=sida, header=sida)
    return render_template('base/tjanster.html')

#endregion

@base_bp.route('/kontakt', methods=['GET', 'POST'])
def kontakt():
    from main import app, mail
    sida = 'Kontakt'
    if request.method == 'POST':
        mail_company = request.form['company']
        mail_firstname = request.form['first_name']
        mail_lastName = request.form['last_name']
        mail_email = request.form['email']
        mail_subject = request.form['subject']
        mail_content = request.form['message']

        newMail = Mail(company = mail_company, first_name = mail_firstname, last_name = mail_lastName,
                       email = mail_email, subject = mail_subject,message=mail_content)
        print(newMail)

        message_body = f"{mail_content} \n" \
                       f"Vänliga Hälsningar {mail_firstname} {mail_lastName}\n" \
                       f"{mail_company}\n{mail_email}"

        message=Message(subject=mail_subject,
                        sender=mail_email,
                        recipients=[app.config['MAIL_USERNAME']],
                        body=message_body)
        mail.send(message)


    return render_template('base/kontakt.html', sida=sida, header=sida)