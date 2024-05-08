from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

#region DataModels
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f'{self.username}, {self.email}, {self.password}'

class BloggPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.String(30), unique=False, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f"{self.author}, {self.title}, {self.content},{self.date}"

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
    activities = db.relationship('Activity', backref='goal', lazy=True)
    def __repr__(self):
        return f"{self.name}"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    measurement = db.Column(db.String(20), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey(Goals.id), nullable=False)

    def __repr__(self):
        return f'{self.name}, {self.measurement}, {self.goal_id}'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Goal = db.Column(db.Integer, db.ForeignKey(Goals.id))
    Activity = db.Column(db.Integer, db.ForeignKey(Activity.id), nullable=False)
    Date = db.Column(db.String(30), nullable=False)
    Time = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f'{self.Goal}, {self.Activity}, {self.Date}, {self.Time}'

class MyWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ord = db.Column(db.String, nullable=False)
    def __repr__(self):
        return f'{self.ord}'
# endregion