#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2  # For PostgreSQL health check
import sqlite3   # For SQLite health check

# Load environment variables
load_dotenv()

# --- SQLAlchemy Compatibility Patch (same as before) ---
if sys.version_info >= (3, 13):
    try:
        from sqlalchemy.util import langhelpers
        # ... [keep the existing patch code] ...
    except ImportError:
        print("SQLAlchemy compatibility patch not needed")

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db').replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "timestamp": datetime.datetime.utcnow().isoformat()
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
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 500

# --- [Rest of your existing routes and models] ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
