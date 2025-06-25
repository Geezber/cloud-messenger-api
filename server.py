#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# SQLAlchemy/Python 3.13 compatibility patch
if sys.version_info >= (3, 13):
    try:
        from sqlalchemy.util import langhelpers
        
        class PatchedTypingOnly:
            __slots__ = ()
            def __init_subclass__(cls, **kwargs):
                allowed = {
                    "__slots__", "__doc__", "__abstract__", 
                    "__firstlineno__", "__static_attributes__",
                    "__annotations__", "__module__", "__dict__",
                    "__weakref__", "__qualname__"
                }
                for key in cls.__dict__:
                    if key not in allowed and not key.startswith(("_abc_", "__orig_bases__")):
                        raise AssertionError(
                            f"Class {cls} has prohibited attribute: {key}"
                        )
                super().__init_subclass__(**kwargs)
        
        langhelpers.TypingOnly = PatchedTypingOnly
        sys.modules['sqlalchemy.util.langhelpers'] = langhelpers
        print("Applied SQLAlchemy 3.13 compatibility patch")
    except ImportError:
        print("SQLAlchemy compatibility patch not needed")

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure database - uses Render's DATABASE_URL environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db').replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Example Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Health check route
@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Application running",
        "python_version": sys.version.split()[0],
        "sqlalchemy_version": db.engine.dialect.dbapi.__version__ if db.engine else "N/A",
        "database": app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]  # Show database type
    })

# Initialize DB - remove in production if using migrations
@app.before_first_request
def initialize_database():
    try:
        db.create_all()
        print("Database tables created")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
