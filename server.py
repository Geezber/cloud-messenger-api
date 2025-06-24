import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure database connection
def get_database_uri():
    # Get DATABASE_URL from environment
    uri = os.environ.get('DATABASE_URL', '')
    
    # Fix common connection string format issues
    if uri.startswith("postgres://"):
        # Convert to SQLAlchemy-compatible format
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    # Fallback to SQLite for local development
    if not uri:
        print("Using SQLite database for local development")
        basedir = os.path.abspath(os.path.dirname(__file__))
        uri = f'sqlite:///{os.path.join(basedir, "local.db")}'
    
    return uri

# Configure application
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db = SQLAlchemy(app)

# Define database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Create database tables
with app.app_context():
    db.create_all()

# Basic route
@app.route('/')
def home():
    return 'Server running successfully with Python 3.13!'

# Health check
@app.route('/health')
def health_check():
    return 'OK', 200

# Entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
