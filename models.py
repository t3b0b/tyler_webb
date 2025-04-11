
from extensions import db
from flask_login import UserMixin
from datetime import datetime
from flask import current_app, Flask
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.associationproxy import association_proxy
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscriber {self.email}>'

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

    #Relationships
    user_goals = db.relationship('Goals', foreign_keys='Goals.user_id', back_populates='user', lazy=True)
    user_activities = db.relationship('Activity', foreign_keys='Activity.user_id', backref='user', lazy=True)
    user_streaks = db.relationship('Streak', foreign_keys='Streak.user_id', back_populates='user', lazy=True)
    user_settings = db.relationship('Settings', foreign_keys='Settings.user_id', back_populates='user', lazy=True)
    friendships = db.relationship('Friendship', foreign_keys='Friendship.user_id', back_populates='user', lazy=True)
    shared_items_owned = db.relationship('SharedItem', back_populates='owner', foreign_keys='SharedItem.owner_id', lazy=True)
    shared_with_items = db.relationship('SharedItem', back_populates='shared_with', foreign_keys='SharedItem.shared_with_id', lazy=True)
    user_scores = db.relationship('Score', foreign_keys='Score.user_id', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}, ID: {self.id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)  # Notifikationsmeddelandet
    related_item_id = db.Column(db.Integer, nullable=True)  # ID för det relaterade objektet (t.ex. mål eller aktivitet)
    item_type = db.Column(db.Enum('goal', 'activity', 'task'), nullable=True)  # Typ av relaterat objekt
    is_read = db.Column(db.Boolean, default=False)  # Om notifikationen är läst
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # När notifikationen skapades
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Mottagarens ID
    #Relationships
    user = db.relationship('User', backref='notifications')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wImp = db.Column(db.Boolean, nullable=False, default=False)
    stInterval = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    user = db.relationship('User', back_populates='user_settings')
    def __repr__(self):
        return f'{self.stInterval}, {self.wImp} ,{self.user_id}'

# endregion

# region Friends
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'blocked'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='friendships')
    friend = db.relationship('User', foreign_keys=[friend_id])

class SharedItem(db.Model):
    __tablename__ = 'shared_items'
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.Enum('goal', 'list', 'streak', 'challenge','event','deadline'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('active', 'completed', 'pending', 'accepted'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #ForiegnKeys
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relationer
    goal = db.relationship('Goals', foreign_keys=[item_id],primaryjoin="and_(SharedItem.item_id == Goals.id, SharedItem.item_type == 'goal')")
    streak = db.relationship('Streak', foreign_keys=[item_id],primaryjoin="and_(SharedItem.item_id == Streak.id, SharedItem.item_type == 'streak')")
    owner = db.relationship('User', foreign_keys=[owner_id], back_populates='shared_items_owned')
    shared_with = db.relationship('User', foreign_keys=[shared_with_id], back_populates='shared_with_items')

    def __repr__(self):
        return f'<SharedItem ID: {self.id}, Owner ID: {self.owner_id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    #ForiegnKeys
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    reciever = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

# endregion

#region Development
class Milestones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    achieved = db.Column(db.Boolean, default=False)
    date_achieved = db.Column(db.DateTime, nullable=True)
    #ForeignKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)  # Koppling till aktivitet
    #Relationships

class Goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    streakCount = db.Column(db.Integer, default=0, nullable=True)
    name = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.String, nullable=True)
    timeLimit = db.Column(db.Integer, nullable=True)
    #ForeignKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #Relationships
    user = db.relationship('User', back_populates='user_goals', lazy=True)
    activities = db.relationship('Activity', backref='activity_goal', lazy=True)
    milestones = db.relationship('Milestones', backref='goal', foreign_keys='Milestones.goal_id', lazy=True)
    deadlines = db.relationship('Deadline', backref='goal', lazy=True)
    events = db.relationship('Event', backref='goal', lazy=True)
    scores = db.relationship('Score', back_populates='goal_score', lazy=True)

    shared_items = association_proxy('shared_items', 'id', creator=lambda goal: SharedItem(item_type='goal', item_id=goal.id))

    def __repr__(self):
        return f"{self.name}, {self.user_id}"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    #ForiegnKeys
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    shared_item_id = db.Column(db.Integer, db.ForeignKey('shared_items.id'), nullable=True) 
    #Relationships
    scores = db.relationship('Score', back_populates='activity_score', lazy=True)
    milestones = db.relationship('Milestones', backref='activity', foreign_keys='Milestones.activity_id', lazy=True)
    shared_item = db.relationship('SharedItem', backref='shared_activities', lazy=True)
    tasks = db.relationship('Tasks', backref='activity', lazy=True)

    def __repr__(self):
        return f"<Activity {self.name}, Goal ID: {self.goal_id}, User ID: {self.user_id}>"
    
class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    time = db.Column(db.Integer, default=0)
    confirmed_date = db.Column(db.DateTime, nullable=True)
    order = db.Column(db.Integer, default=0)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    shared_item_id = db.Column(db.Integer, db.ForeignKey('shared_items.id'), nullable=True)  # Koppling till delning
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    #Relationships
    is_repeatable = db.Column(db.Boolean, nullable=False, default=False)
    total_repeats = db.Column(db.Integer, nullable=True)
    completed_repeats = db.Column(db.Integer, nullable=True, default=0)

    shared_item = db.relationship('SharedItem', backref='tasks')
    subtasks = db.relationship('SubTask', backref='tasks', lazy=True)

    def add_repeat(self):
        if self.is_repeatable and self.total_repeats is not None:
            self.completed_repeats += 1
            if self.completed_repeats >= self.total_repeats:
                self.completed = True

class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Namnet på subtasken
    completed = db.Column(db.Boolean, default=False)  # Om subtasken är klar
    order = db.Column(db.Integer, default=0)
    #ForiegnKeys
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)  # Koppling till huvudtasken
    #Relationships
    def __repr__(self):
        return f"<SubTask {self.name}, Completed: {self.completed}>"

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
    level = db.Column(db.Integer, nullable=True, default=1)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)
    #Relationships
    streak_score = db.relationship('Score', backref='streak', lazy=True)
    shared_items = association_proxy('shared_items', 'id', creator=lambda streak: SharedItem(item_type='streak', item_id=streak.id))
    user = db.relationship('User', back_populates='user_streaks', lazy=True)
    def __repr__(self):
        return f"{self.name}, {self.interval}, {self.count}, {self.goal_id}, {self.best}, {self.condition}, {self.lastReg}, {self.dayOne}, {self.user_id}"

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Amount = db.Column(db.Integer, nullable=True)
    Start = db.Column(db.DateTime, nullable=True)
    End = db.Column(db.DateTime, nullable=True)
    Date = db.Column(db.DateTime, nullable=False)
    Time = db.Column(db.Integer, nullable=False)
    #ForiegnKeys
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    streak_id = db.Column(db.Integer, db.ForeignKey('streak.id'), nullable=True)
    #Relationships
    goal_score = db.relationship('Goals', back_populates='scores', lazy=True)
    activity_score = db.relationship('Activity', back_populates='scores', lazy=True)

    def __repr__(self):
        return f'{self.goal_id}, {self.activity_id}, {self.Date}, {self.Time}, {self.user_id}'

# endregion

# region Calendar

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(20))  # event, milestone, deadline
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(255), nullable=True)  # Lägg till plats som en sträng
    date = db.Column(db.Date, nullable=False)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)
    #Relationships
    is_recurring = db.Column(db.Boolean, default=False)  # Om eventet repeteras
    recurrence_type = db.Column(db.String(20), nullable=True)  # 'daily', 'weekly', 'monthly'
    recurrence_interval = db.Column(db.Integer, nullable=True)  # Exempel: 1 = varje vecka, 2 = varannan vecka

    def __repr__(self):
        return f'{self.name} on {self.date} at {self.location}'

class Deadline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date, nullable=True)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'))
    #Relationships
    def __repr__(self):
        return f'{self.name} - Due: {self.due_date}'
    
# endregion

#region Text

class TopFive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    content = db.Column(db.String(1200), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    list_type = db.Column(db.String(50), nullable=False, default="top_five_today")
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #Relationships
    def __repr__(self):
        return f"<CalendarBullet {self.date}>"

class Lists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=True)
    date = db.Column(db.Date, unique=False, nullable=False, default=datetime.utcnow)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #Relationships
    shared_items = association_proxy('shared_items', 'id',
                                     creator=lambda bullet: SharedItem(item_type='list', item_id=bullet.id))

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    author = db.Column(db.String(50), nullable=True)
    type = db.Column(db.Integer, nullable=True)
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False )
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)
    #Relationships
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
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #Relationships

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
    #ForiegnKeys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #Relationships

    def __repr__(self):
        return f"{self.company},{self.first_name},{self.last_name},{self.email},{self.subject},{self.message}"