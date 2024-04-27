from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from flask import request, redirect, url_for
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import sqlite3
import pandas as pd

app = Flask(__name__)

app.config['SECRET_KEY'] = "K6SM4x14"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tylerobri.db"
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "pmg.automatic.services@gmail.com"
app.config['MAIL_PASSWORD'] = "gygfvycgvmjybgse"
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
mail = Mail(app)
connection = sqlite3.connect("instance/tylerobri.db")

def readinfo(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


class User(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    def __repr__(self):
        return f"{self.name}, {self.password}"
class BloggPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.String(30), unique=False, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f"{self.author}, {self.topic}, {self.sub_topic}, {self.title}, {self.content},{self.date}"

class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    best = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(80),nullable=False)
    lastReg = db.Column(db.String(50), nullable=False)
    dayOne = db.Column(db.String(50), nullable=False)
    def __repr__(self):
        return f"{self.name}, {self.priority}, {self.count}, {self.best}, {self.condition}, {self.lastReg}, {self.dayOne} "

class Goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    def __repr__(self):
        return f"{self.name}"


myUser = User(name="Tyler O'Brien", password='K6SM4x12')

with app.app_context():
    db.create_all()
    db.session.add(myUser)
    db.session.commit()
@app.route('/')
def home():
    sida="Hem"
    return render_template('home.html',sida=sida,header="Tyler O'Brien")

@app.route('/blogg',methods=['GET', 'POST'])
def blogg():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida="Blogg"
    ord=readinfo('orden.txt')
    orden=ord.split('\n')

    if request.method=='POST':
        post_author="Tyler O'Brien"
        post_ord = request.form['post-ord']
        post_text = request.form['blogg-content']
        post_date = current_date

        newPost = BloggPost(author=post_author, title=post_ord,
                            content=post_text,date=post_date)
        db.session.add(newPost)
        db.session.commit()

    return render_template('blogg.html',sida=sida,header=sida,orden=orden)


@app.route('/pmgloggin',methods=['GET', 'POST'])
def loggin():
    return render_template('pmg-loggin.html')

@app.route('/streak',methods=['GET', 'POST'])
def streak():
    current_date = datetime.now().strftime("%Y-%m-%d")
    sida="Mina Streaks"
    myStreaks = Streak.query.all()
    print(myStreaks)
    if request.method == 'POST':
        Streak_name = request.form['streakName']
        Streak_dayOne = request.form['streakStart']
        Streak_priority = request.form['streakPriority']
        Streak_condition = request.form['streakConditions']
        newStreak = Streak(name=Streak_name, priority=Streak_priority, count=1,
                           best=1,condition=Streak_condition, lastReg=Streak_dayOne,
                           dayOne=Streak_dayOne)

        db.session.add(newStreak)
        db.session.commit()
        return redirect(url_for('streak'),sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)
    return render_template('streak.html',sida=sida,header=sida,todayDate=current_date,streaks=myStreaks)

@app.route('/goals',methods=['GET', 'POST'])
def goals():
    myGoals = Goals.query.all()
    sida = "Mina Mål"
    return render_template('goals.html',sida=sida,header=sida, goals=myGoals)

@app.route('/myday')
def myday():
    sida = "Min Dag"
    return render_template('myday.html',sida=sida,header=sida)

@app.route('/month')
def month():
    # Det nuvarande året och månaden
    year = datetime.now().year
    month = datetime.now().month

    # Första dagen i månaden och månadens namn
    first_day_of_month = datetime(year, month, 1)
    month_name = first_day_of_month.strftime('%B')

    # Skapa en lista som representerar dagarna i månaden, inklusive föregående och nästkommande månad
    days = []
    # Föregående månad
    previous_month_day = first_day_of_month - timedelta(days=1)
    while previous_month_day.weekday() != 6:  # Söndag är 6 i weekday() funktionen
        days.insert(0, {'day': previous_month_day.day, 'date': previous_month_day, 'current_month': False})
        previous_month_day -= timedelta(days=1)

    # Aktuell månad
    current_day = first_day_of_month
    while current_day.month == month:
        days.append({'day': current_day.day, 'date': current_day, 'current_month': True})
        current_day += timedelta(days=1)

    # Nästkommande månad
    while len(days) % 7 != 0:
        days.append({'day': current_day.day, 'date': current_day, 'current_month': False})
        current_day += timedelta(days=1)

    # Dela upp dagarna i veckor
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    # Titeln och headern för sidan
    sida = "Min Månad"
    return render_template('month.html', weeks=weeks, month_name=month_name, year=year, sida=sida, header=sida)

if __name__ == '__main__':
    app.run(debug=True)