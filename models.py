from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

#region DataModels
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return f'{self.username}, {self.email}, {self.password}'

class Dagbok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    def __repr__(self):
        return f"{self.user_id},{self.author},{self.title},{self.content}"

class BloggPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.String(30), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __repr__(self):
        return f"{self.author}, {self.title}, {self.content},{self.date}, {self.user_id}"

class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    interval = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    goal = db.Column(db.Integer, nullable=True)
    best = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(80),nullable=False)
    lastReg = db.Column(db.String(50), nullable=False)
    dayOne = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"{self.name}, {self.interval}, {self.count}, {self.goal}, {self.best}, {self.condition}, {self.lastReg}, {self.dayOne}, {self.user_id}"

class Goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    activities = db.relationship('Activity', backref='goal', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"{self.name}, {self.user_id}"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    measurement = db.Column(db.String(20), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey(Goals.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.name}, {self.measurement}, {self.goal_id}, {self.user_id}'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Goal = db.Column(db.Integer, db.ForeignKey(Goals.id))
    Activity = db.Column(db.Integer, db.ForeignKey(Activity.id), nullable=False)
    Date = db.Column(db.String(30), nullable=False)
    Time = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.Goal}, {self.Activity}, {self.Date}, {self.Time}, {self.user_id}'

class MyWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ord = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.ord}, {self.user_id}'

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stInterval=db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.stInterval}, {self.user_id}'


class Dagar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    total_streaks = db.Column(db.Integer)
    completed_streaks = db.Column(db.Integer)
    completed_streaks_names = db.Column(db.Text)
    total_points = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'{self.user_id}, {self.date}, {self.total_streaks}, {self.completed_streaks}, {self.completed_streaks_names}, {self.total_points}'

# endregion