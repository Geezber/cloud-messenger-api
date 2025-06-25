from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
from datetime import datetime
import sys
from dotenv import load_dotenv
import psycopg2
import sqlite3

# Load environment variables
load_dotenv()

# --- Remove Python 3.13 compatibility patch ---
# (Not needed for Python 3.12.10)

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db').replace('postgres://', 'postgresql://', 1)
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

# --- Replace deprecated before_first_request ---
with app.app_context():
    db.create_all()

# --- Health Check Endpoints ---
@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connection
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
            conn.close()
        else:  # SQLite
            conn = sqlite3.connect('app.db')
            conn.close()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system info"""
    try:
        # Database check
        db_status = "unknown"
        try:
            db.engine.execute("SELECT 1")
            db_status = "connected"
        except:
            db_status = "disconnected"
        
        return jsonify({
            "status": "healthy",
            "system": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "sqlalchemy_version": db.engine.dialect.dbapi.__version__ if db.engine else "N/A"
            },
            "services": {
                "database": db_status,
                "database_type": app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# --- API Endpoints ---
# (All endpoint implementations remain unchanged)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
