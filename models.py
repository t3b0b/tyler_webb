
from flask_login import UserMixin
from datetime import datetime
from flask import current_app, Flask
from sqlalchemy.dialects.postgresql import JSON
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tylerobri:Tellus420@tylerobri.mysql.pythonanywhere-services.com/tylerobri$PMG'
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, default=False)

    shared_goals = db.relationship('SharedGoal', secondary='shared_goal_user', back_populates='users')
    shared_streaks = db.relationship('SharedStreak', secondary='shared_streak_user', back_populates='users')

    friends = db.relationship('User',
                               secondary='friendship',
                               primaryjoin='User.id==Friendship.user_id',
                               secondaryjoin='User.id==Friendship.friend_id',
                               backref='friend_of')
    def __repr__(self):
        return f'{self.username}, {self.email}, {self.password}'

class Friendship(db.Model):
    __tablename__ = 'friendship'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    status = db.Column(db.String(50), nullable=False)  # pending, accepted

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Uppdatera till receiver_id
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    reciever = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
# endregion


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wImp = db.Column(db.Boolean, nullable=False, default=False)
    stInterval = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'{self.stInterval}, {self.wImp} ,{self.user_id}'

# endregion

#region Development
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

class SharedGoalUser(db.Model):
    __tablename__ = 'shared_goal_user'
    goal_id = db.Column(db.Integer, db.ForeignKey('shared_goal.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)  # ForeignKey till goals
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey till user
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)

    # Lägg till relation till ToDoList via ForeignKey
    todo_list = db.relationship('ToDoList', backref='activity', lazy=True)
    tasks = db.relationship('Task', back_populates='activity')

# Koppling till att-göra-lista och tasks
class ToDoList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Tilldelad användare
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)    # Den som markerade uppgiften som klar
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Bekräftad av den andra användaren
    confirmed_date = db.Column(db.DateTime, nullable=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relations
    activity = db.relationship('Activity', back_populates='tasks')

class Milestones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=False)  # Estimated time in minutes
    deadline = db.Column(db.DateTime, nullable=True)
    achieved = db.Column(db.Boolean, default=False)
    date_achieved = db.Column(db.DateTime, nullable=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)

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

class SharedGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    users = db.relationship('User', secondary='shared_goal_user', back_populates='shared_goals')

class SharedStreak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.String(50), nullable=False)  # daily, weekly etc.
    current_turn_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    users = db.relationship('User', secondary='shared_streak_user', back_populates='shared_streaks')
class SharedStreakUser(db.Model):
    __tablename__ = 'shared_streak_user'
    streak_id = db.Column(db.Integer, db.ForeignKey('shared_streak.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    last_checkin_date = db.Column(db.DateTime, nullable=True)

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

# region Friends

# region Calendar

class TopFive(db.Model):
    __tablename__ = 'top_five'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    content = db.Column(db.String(1200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f"<CalendarBullet {self.date}>"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(20))  # event, milestone, deadline
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'{self.name} on {self.date}'


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

# endregion

#region Text

class Bullet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=True)
    date = db.Column(db.Date, unique=False, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, unique=False, nullable=False)
    author = db.Column(db.String(50), nullable=True)
    type = db.Column(db.Integer, nullable=False)
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

