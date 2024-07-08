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
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'{self.username}, {self.email}, {self.password}'

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), nullable=False)  # t.ex., 'pending', 'accepted', 'declined'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Dagbok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    def __repr__(self):
        return f"{self.user_id},{self.author},{self.title},{self.content}"

class BusinessBlogg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    sub_topic = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.author}, {self.topic}, {self.sub_topic}, {self.title}, {self.content},{self.date}"

class Bullet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class BloggPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __repr__(self):
        return f"{self.author}, {self.title}, {self.content},{self.date}, {self.user_id}"

class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, nullable=True)
    interval = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    best = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(80),nullable=False)
    lastReg = db.Column(db.DateTime, nullable=False)
    dayOne = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Integer, default=0)
    type = db.Column(db.String(20), default='check', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)
    level = db.Column(db.Integer, nullable=True, default=1)
    def __repr__(self):
        return f"{self.name}, {self.interval}, {self.count}, {self.goal}, {self.best}, {self.condition}, {self.lastReg}, {self.dayOne}, {self.user_id}"

class Milestones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=False)  # Estimated time in minutes
    deadline = db.Column(db.DateTime, nullable=True)
    achieved = db.Column(db.Boolean, default=False)
    date_achieved = db.Column(db.DateTime, nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    activities = db.relationship('Activity', backref='milestones', lazy=True)

class Goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.String, nullable=True)
    timeLimit = db.Column(db.Integer, nullable=True)
    activities = db.relationship('Activity', backref='goal', lazy=True)
    milestones = db.relationship('Milestones', backref='goal', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"{self.name}, {self.user_id}"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __repr__(self):
        return f'{self.name}, {self.unit}, {self.goal_id}, {self.user_id}'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Goal = db.Column(db.Integer, db.ForeignKey(Goals.id))
    Activity = db.Column(db.Integer, db.ForeignKey(Activity.id), nullable=False)
    Amount = db.Column(db.Integer, nullable=True)
    Start = db.Column(db.DateTime, nullable=True)
    End = db.Column(db.DateTime, nullable=True)
    Date = db.Column(db.DateTime, nullable=False)
    Time = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    Streak = db.Column(db.Integer, db.ForeignKey('streak.id'), nullable=False)
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
    wImp = db.Column(db.Boolean, nullable=False, default=False)
    stInterval = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.stInterval}, {self.user_id}'

class Dagar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, unique=True)
    prioriteringar = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_streaks = db.Column(db.Integer)
    completed_streaks = db.Column(db.Integer)
    completed_streaks_names = db.Column(db.Text)
    total_points = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'{self.user_id}, {self.date}, {self.total_streaks}, {self.completed_streaks}, {self.completed_streaks_names}, {self.total_points}'

class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(80), nullable=False)
    viktigt = db.Column(db.Text, nullable=True)
    tankar = db.Column(db.Text, nullable=True)
    remember = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.month}, {self.viktigt}, {self.tankar}, {self.remember}'
class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    viktigt = db.Column(db.Text, nullable=True)
    tankar = db.Column(db.Text, nullable=True)
    remember = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.week}, {self.viktigt}, {self.tankar}, {self.remember}'

class Idag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    viktigt = db.Column(db.Text, nullable=True)
    tankar = db.Column(db.Text, nullable=True)
    remember = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.date}, {self.viktigt}, {self.tankar}, {self.remember}'

class Mail(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(80))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(80))
    subject = db.Column(db.String(50))
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"{self.company},{self.first_name},{self.last_name},{self.email},{self.subject},{self.message}"

# endregion

