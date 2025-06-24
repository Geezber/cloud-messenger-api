import os
import re
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configure database URI
def get_database_uri():
    # Get DATABASE_URL from environment (provided by Render)
    uri = os.environ.get('DATABASE_URL', '')
    
    # Fix common connection string format issues
    if uri.startswith("postgres://"):
        # Convert to SQLAlchemy-compatible format with psycopg v3 driver
        uri = uri.replace("postgres://", "postgresql+psycopg://", 1)
    
    # Fallback to SQLite for local development if no URI provided
    if not uri:
        print("WARNING: Using SQLite database for local development")
        basedir = os.path.abspath(os.path.dirname(__file__))
        uri = f'sqlite:///{os.path.join(basedir, "local.db")}'
    
    return uri

# Configure application
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Helps with connection recycling
    'pool_recycle': 300,    # Recycle connections every 5 minutes
}

# Initialize database
db = SQLAlchemy(app)

# Define database model (example)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()

# Basic route
@app.route('/')
def home():
    return 'Server is running successfully!'

# Health check endpoint
@app.route('/health')
def health_check():
    return 'OK', 200

# Entry point for running the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
