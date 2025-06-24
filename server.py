from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
from datetime import datetime
from sqlalchemy import and_, or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    token = db.Column(db.String(36), unique=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self):
        self.token = str(uuid.uuid4())
        return self.token

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'contact_id', name='_user_contact_uc'),)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'text' or 'voice'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

@app.before_first_request
def create_tables():
    db.create_all()

# API Endpoints
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=username)
    user.set_password(password)
    token = user.generate_token()
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'token': token,
        'user_id': user.id
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    token = user.generate_token()
    db.session.commit()
    
    return jsonify({
        'token': token,
        'user_id': user.id
    })

@app.route('/search', methods=['GET'])
def search():
    token = request.args.get('token')
    username = request.args.get('username')
    
    if not token:
        return jsonify({'error': 'Token required'}), 401
    
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    
    if not username:
        return jsonify({'users': []})
    
    users = User.query.filter(
        User.username.ilike(f'%{username}%'),
        User.id != user.id
    ).all()
    
    user_list = [{'id': user.id, 'username': user.username} for user in users]
    return jsonify({'users': user_list})

@app.route('/add_contact', methods=['POST'])
def add_contact():
    data = request.json
    token = data.get('token')
    contact_id = data.get('contact_id')
    
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    
    contact = User.query.get(contact_id)
    if not contact:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if contact already exists
    existing = Contact.query.filter_by(user_id=user.id, contact_id=contact_id).first()
    if existing:
        return jsonify({'error': 'Contact already added'}), 400
    
    # Add contact
    contact_entry = Contact(user_id=user.id, contact_id=contact_id)
    db.session.add(contact_entry)
    
    # Add reverse contact for bi-directional
    reverse_contact = Contact(user_id=contact_id, contact_id=user.id)
    db.session.add(reverse_contact)
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/contacts', methods=['GET'])
def get_contacts():
    token = request.args.get('token')
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    
    contacts = Contact.query.filter_by(user_id=user.id).all()
    contact_list = []
    for contact in contacts:
        contact_user = User.query.get(contact.contact_id)
        if contact_user:  # Ensure contact exists
            contact_list.append(contact_user.username)
    
    return jsonify({'contacts': contact_list})

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    token = data.get('token')
    recipient = data.get('recipient')
    message_type = data.get('type')
    content = data.get('content')
    
    sender = User.query.filter_by(token=token).first()
    if not sender:
        return jsonify({'error': 'Invalid token'}), 401
    
    recipient_user = User.query.filter_by(username=recipient).first()
    if not recipient_user:
        return jsonify({'error': 'Recipient not found'}), 404
    
    # Save message
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_user.id,
        type=message_type,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({'success': True, 'message_id': msg.id})

@app.route('/messages', methods=['GET'])
def get_messages():
    token = request.args.get('token')
    last_id = request.args.get('last_id', 0, type=int)
    
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    
    messages = Message.query.filter(
        Message.recipient_id == user.id,
        Message.id > last_id
    ).order_by(Message.id.asc()).all()
    
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'id': msg.id,
            'sender': sender.username,
            'type': msg.type,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        })
    
    return jsonify({'messages': result})

if __name__ == '__main__':
    app.run(debug=True)