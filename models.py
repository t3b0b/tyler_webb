
from extensions import db
from flask_login import UserMixin
from datetime import datetime
from flask import current_app, Flask
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.associationproxy import association_proxy
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

#region User

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    profilePic = db.Column(db.String(150), default=None, nullable=True)  # Kolumn för profilbild

    # Justera namnet på backref till 'user_friendships' istället för 'user'
    friendships = db.relationship('Friendship', foreign_keys='Friendship.user_id', backref='user_friendships', lazy=True)
    shared_items = db.relationship('SharedItem', foreign_keys='SharedItem.owner_id', backref='user_shared_items', lazy=True)

    def __repr__(self):
        return f'<User {self.username}, ID: {self.id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Mottagarens ID
    message = db.Column(db.String(255), nullable=False)  # Notifikationsmeddelandet
    related_item_id = db.Column(db.Integer, nullable=True)  # ID för det relaterade objektet (t.ex. mål eller aktivitet)
    item_type = db.Column(db.Enum('goal', 'activity', 'task'), nullable=True)  # Typ av relaterat objekt
    is_read = db.Column(db.Boolean, default=False)  # Om notifikationen är läst
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # När notifikationen skapades

    user = db.relationship('User', backref='notifications')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wImp = db.Column(db.Boolean, nullable=False, default=False)
    stInterval = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.stInterval}, {self.wImp} ,{self.user_id}'

# endregion

# region Friends
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'blocked'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    friend = db.relationship('User', foreign_keys=[friend_id])

class SharedItem(db.Model):
    __tablename__ = 'shared_items'
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.Enum('goal', 'list', 'streak', 'challenge'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('active', 'completed', 'pending', 'accepted'), default='active')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationer
    goal = db.relationship('Goals', foreign_keys=[item_id],
                           primaryjoin="and_(SharedItem.item_id == Goals.id, SharedItem.item_type == 'goal')")
    streak = db.relationship('Streak', foreign_keys=[item_id],
                             primaryjoin="and_(SharedItem.item_id == Streak.id, SharedItem.item_type == 'streak')")
    owner = db.relationship('User', foreign_keys=[owner_id], backref='shared_items_owned')
    shared_with = db.relationship('User', foreign_keys=[shared_with_id], backref='shared_with_items')

    def __repr__(self):
        return f'<SharedItem ID: {self.id}, Owner ID: {self.owner_id}>'

class ActivityTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('shared_items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.Enum('task_completed', 'streak_maintained', 'challenge_participated'),
                              nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationer
    item = db.relationship('SharedItem', backref='activities')
    user = db.relationship('User', backref='activities')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Uppdatera till receiver_id
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    reciever = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
# endregion

#region Development

class Goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    streakCount = db.Column(db.Integer, default=0, nullable=True)
    name = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.String, nullable=True)
    timeLimit = db.Column(db.Integer, nullable=True)
    activities = db.relationship('Activity', backref='goal', lazy=True)
    milestones = db.relationship('Milestones', backref='goal', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shared_items = association_proxy('shared_items', 'id', creator=lambda goal: SharedItem(item_type='goal', item_id=goal.id))

    def __repr__(self):
        return f"{self.name}, {self.user_id}"

class Milestones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=False)  # Estimated time in minutes
    deadline = db.Column(db.DateTime, nullable=True)
    achieved = db.Column(db.Boolean, default=False)
    date_achieved = db.Column(db.DateTime, nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)  # ForeignKey till goals
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey till user
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    
    shared_item_id = db.Column(db.Integer, db.ForeignKey('shared_items.id'), nullable=True)  # Koppling till shared_items
    shared_item = db.relationship('SharedItem', backref='shared_activities', lazy=True)

    todo_list = db.relationship('Tasks', backref='activity', lazy=True)

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    shared_item_id = db.Column(db.Integer, db.ForeignKey('shared_items.id'), nullable=True)  # Koppling till delning
    time = db.Column(db.Integer, default=0)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    confirmed_date = db.Column(db.DateTime, nullable=True)
    order = db.Column(db.Integer, default=0)

    is_repeatable = db.Column(db.Boolean, nullable=False, default=False)
    total_repeats = db.Column(db.Integer, nullable=True)
    completed_repeats = db.Column(db.Integer, nullable=True, default=0)

    shared_item = db.relationship('SharedItem', backref='tasks')
    subtasks = db.relationship('SubTask', backref='tasks', lazy=True)

    def add_repeat(self):
        if self.is_repeatable:
            self.completed_repeats += 1
            if self.completed_repeats >= self.total_repeats:
                self.completed = True

class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Namnet på subtasken
    completed = db.Column(db.Boolean, default=False)  # Om subtasken är klar
    order = db.Column(db.Integer, default=0)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)  # Koppling till huvudtasken

    def __repr__(self):
        return f"<SubTask {self.name}, Completed: {self.completed}>"

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscriber {self.email}>'

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
    shared_items = association_proxy('shared_items', 'id', creator=lambda streak: SharedItem(item_type='streak', item_id=streak.id))

    def __repr__(self):
        return f"{self.name}, {self.interval}, {self.count}, {self.goal_id}, {self.best}, {self.condition}, {self.lastReg}, {self.dayOne}, {self.user_id}"

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

# endregion

# region Calendar

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(20))  # event, milestone, deadline
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(255), nullable=True)  # Lägg till plats som en sträng
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)

    is_recurring = db.Column(db.Boolean, default=False)  # Om eventet repeteras
    recurrence_type = db.Column(db.String(20), nullable=True)  # 'daily', 'weekly', 'monthly'
    recurrence_interval = db.Column(db.Integer, nullable=True)  # Exempel: 1 = varje vecka, 2 = varannan vecka

    def __repr__(self):
        return f'{self.name} on {self.date} at {self.location}'

# endregion

#region Text

class TopFive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    content = db.Column(db.String(1200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    list_type = db.Column(db.String(50), nullable=False, default="top_five_today")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"<CalendarBullet {self.date}>"

class Bullet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=True)
    date = db.Column(db.Date, unique=False, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shared_items = association_proxy('shared_items', 'id',
                                     creator=lambda bullet: SharedItem(item_type='bullet', item_id=bullet.id))

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    author = db.Column(db.String(50), nullable=True)
    type = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)

    def __repr__(self):
        return f"{self.author}, {self.title}, {self.content},{self.date}, {self.user_id}"

class MyWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(120), nullable=False)
    what = db.Column(db.Boolean, nullable=False,default=False)
    why = db.Column(db.Boolean, nullable=False, default=False)
    when = db.Column(db.Boolean, nullable=False, default=False)
    how = db.Column(db.Boolean, nullable=False, default=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.word}, {self.used},{self.user_id}'

# endregion

class Mail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(80))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(80))
    subject = db.Column(db.String(50))
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f"{self.company},{self.first_name},{self.last_name},{self.email},{self.subject},{self.message}"