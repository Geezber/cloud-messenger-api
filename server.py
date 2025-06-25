#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

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

# Configure database - UPDATE THIS FOR YOUR PROJECT
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Example Model - MODIFY FOR YOUR PROJECT
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Example Route - MODIFY FOR YOUR PROJECT
@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Application running",
        "python_version": sys.version.split()[0],
        "sqlalchemy_version": db.engine.dialect.dbapi.__version__
    })

# Initialize DB (use carefully in production)
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
