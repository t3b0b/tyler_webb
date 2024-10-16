from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from models import User, Friendship, Message, db

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
    friendships = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id))
        & (Friendship.status == 'accepted')
    ).all()

    all_messages = {}

    for friendship in friendships:
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
    flash('Vänförfrågan har skickats.', 'success')
    return redirect(url_for('friends.users'))

@friends_bp.route('/friends')
@login_required
def friends():
    sida,sub_menu=common_route('Friends',['/friends/friends','/friends/all_messages','/friends/users'],['Friends','Messages','Users'])

    pending_requests = Friendship.query.filter_by(friend_id=current_user.id, status='pending').all()
    accepted_friends = Friendship.query.filter_by(user_id=current_user.id, status='accepted').all() + \
                       Friendship.query.filter_by(friend_id=current_user.id, status='accepted').all()
    
    pending_users = User.query.filter(User.id.in_(pending_requests)).all()
    accepted_users = User.query.filter(User.id.in_(accepted_friends)).all()

    return render_template('friends.html', pending_users=pending_users, accepted_users=accepted_users, 
                           pending_requests=pending_requests, accepted_friends=accepted_friends)

@friends_bp.route('/respond_friend_request/<int:request_id>/<response>')
@login_required
def respond_friend_request(request_id, response):
    friendship = Friendship.query.get_or_404(request_id)
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
            # Kontrollera att användarna är vänner
            if recipient in current_user.friends:
                message = Message(sender_id=current_user.id, recipient_id=recipient.id, content=content)
                db.session.add(message)
                db.session.commit()
                flash('Meddelande skickat!', 'success')
                return redirect(url_for('messaging.view_messages', user_id=recipient.id))
            else:
                flash('Ni är inte vänner och kan därför inte skicka meddelanden.', 'danger')
                return redirect(url_for('main.index'))
    return render_template('/friends/sendMsg.html', recipient=recipient)

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