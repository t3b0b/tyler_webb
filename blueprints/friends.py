from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import mail,db
from datetime import datetime, timedelta, date
from models import User, Friendship, Message, Notification
from pmg_func import create_notification

friends_bp = Blueprint('friends', __name__)

def common_route(title,sub_url,sub_text):
    sida = title
    sub_menu = []
    if sub_text:
        for i, url in enumerate(sub_url):
            sub_menu.append({
                 'choice': url,
                 'text': sub_text[i]
            })
        return sida, sub_menu
    else:
        return sida, None

@friends_bp.route('/all_messages')
@login_required
def all_messages():
    sida,sub_menu = common_route('Messages',['/friends/friends','/friends/all_messages','/friends/users'],['Friends','Messages','Users'])
    friends = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id))
        & (Friendship.status == 'accepted')
    ).all()

    all_messages = {}

    for friendship in friends:
        if friendship.user_id == current_user.id:
            friend_id = friendship.friend_id
        else:
            friend_id = friendship.user_id

        friend = User.query.get(friend_id)

        sent_messages = Message.query.filter_by(sender_id=current_user.id, recipient_id=friend_id).all()
        received_messages = Message.query.filter_by(sender_id=friend_id, recipient_id=current_user.id).all()

        messages = sorted(sent_messages + received_messages, key=lambda x: x.timestamp)
        all_messages[friend] = messages

    return render_template('friends/all_messages.html', all_messages=all_messages,sida=sida,header=sida,sub_menu=sub_menu)
@friends_bp.route('/users')
@login_required
def users():

    sida,sub_menu = common_route('Add Friends',['/friends/friends','/friends/all_messages','/friends/users'],['Friends','Messages','Users'])
    all_users = User.query.filter(User.id != current_user.id).all()  # Exkludera den inloggade användaren

    return render_template('/friends/users.html', users=all_users,sida=sida,header=sida,sub_menu=sub_menu)

@friends_bp.route('/friend_profile/<int:user_id>', methods=['POST'])
@login_required
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    sida, sub_menu = common_route(f'{user.firstName} {user.lastName}',
                                  ['/pmg/streak', '/pmg/goals', '/pmg/milestones'], ['Streaks', 'Goals', 'Milestones'])
    return render_template('/friends/friend_profile.html',user=user,sida=sida,header=sida)

@friends_bp.route('/add_friend/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    friend = User.query.get_or_404(friend_id)
    if friend == current_user:
        flash('Du kan inte lägga till dig själv som vän.', 'danger')
        return redirect(url_for('friends.users'))

    existing_friendship = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
    if existing_friendship:
        flash('Vänförfrågan har redan skickats.', 'warning')
        return redirect(url_for('friends.users'))

    new_friendship = Friendship(user_id=current_user.id, friend_id=friend.id, status='pending')
    db.session.add(new_friendship)
    db.session.commit()

    create_notification(
        user_id=friend_id,  # Mottagarens ID
        message=f"{current_user.username} wants to be your friend",
        related_item_id=new_friendship.id,
        item_type='friend'
    )

    flash('Vänförfrågan har skickats.', 'success')
    return redirect(url_for('friends.users'))

@friends_bp.route('/friends')
@login_required
def friends():
    sida, sub_menu = common_route('Friends', ['/friends/friends', '/friends/all_messages', '/friends/users'], ['Friends', 'Messages', 'Users'])
    
    pending_requests = Friendship.query.filter_by(friend_id=current_user.id, status='pending').all()
    accepted_friends = Friendship.query.filter_by(user_id=current_user.id, status='accepted').all() + \
                       Friendship.query.filter_by(friend_id=current_user.id, status='accepted').all()

    # Extrahera id från pending_requests och accepted_friends
    pending_user_ids = [request.user_id for request in pending_requests]
    accepted_user_ids = [friend.user_id if friend.user_id != current_user.id else friend.friend_id for friend in accepted_friends]

    # Hämta användarna baserat på id-listorna
    pending_users = User.query.filter(User.id.in_(pending_user_ids)).all()
    friends = User.query.filter(User.id.in_(accepted_user_ids)).all()
    users = User.query.filter(
        User.id != current_user.id,  # Exkludera den inloggade användaren
        ~User.id.in_(accepted_user_ids)  # Exkludera accepterade vänner
    ).all()

    return render_template('/friends/friends.html', sida=sida, sub_menu=sub_menu, pending_users=pending_users, friends=friends, users=users)

@friends_bp.route('/respond_friend_request/<int:request_id>/<response>', methods=['POST'])
@login_required
def respond_friend_request(request_id, response):
    friendship = Friendship.query.filter_by(user_id=request_id, friend_id=current_user.id).first_or_404()
    if friendship.friend_id != current_user.id: 
        flash('Not authorized.', 'danger')
        return redirect(url_for('pmg.myday'))
    if response == 'accept':
        friendship.status = 'accepted'
        db.session.commit()
        flash('Friend request accepted.', 'success')
    elif response == 'decline':
        db.session.delete(friendship)
        db.session.commit()
        flash('Friend request declined.', 'danger')

    return redirect(url_for('friends.friends'))

@friends_bp.route('/send_message/<int:recipient_id>', methods=['GET', 'POST'])
@login_required
def send_message(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            message = Message(
                sender_id=current_user.id,
                receiver_id=recipient_id,  # Korrigerat stavfel här
                content=content,
                timestamp=datetime.now()
            )
            db.session.add(message)
            db.session.commit()

            create_notification(
                user_id=recipient_id,  # Mottagarens ID
                message=f"{current_user.username} sent you a message",
                related_item_id=message.id,
                item_type='message'
            )
            flash('Message sent successfully.', 'success')
            return redirect(url_for('friends.send_message', recipient_id=recipient_id))
    
    # Hämta alla meddelanden mellan användare i båda riktningarna (som en konversation)
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) & (Message.receiver_id == recipient_id) |
        (Message.sender_id == recipient_id) & (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp).all()

    return render_template('friends/sendMsg.html', recipient=recipient, messages=messages)

@friends_bp.route('/messages/<int:user_id>')
@login_required
def view_messages(user_id):
    user = User.query.get_or_404(user_id)
    if user in current_user.friends:
        sent_messages = Message.query.filter_by(sender_id=current_user.id, recipient_id=user.id).all()
        received_messages = Message.query.filter_by(sender_id=user.id, recipient_id=current_user.id).all()
        messages = sorted(sent_messages + received_messages, key=lambda x: x.timestamp)
        return render_template('/friends/viewMsg.html', messages=messages, user=user)
    else:
        flash('Ni är inte vänner och kan därför inte se meddelanden.', 'danger')
        return redirect(url_for('main.index'))