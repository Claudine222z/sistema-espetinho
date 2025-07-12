#!/usr/bin/env python3
"""
WSGI entry point for Sistema Espetinho
This file is used by Gunicorn in production
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app, db
    from render_config import apply_render_config
    
    # Initialize database and create admin user
    with app.app_context():
        try:
            # Create database tables if they don't exist
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create admin user if it doesn't exist
            from app import User
            from werkzeug.security import generate_password_hash
            
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    nome='Administrador',
                    email='admin@espetinho.com',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário admin criado!")
            else:
                print("✅ Usuário admin já existe!")
                
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
    
    # Apply Render-specific configuration
    apply_render_config(app)
    
    # Export the app for Gunicorn
    application = app
    print("✅ WSGI application loaded successfully")
    print("🌐 Production configuration applied")
    print("🔒 HTTPS and secure cookies enabled")
    
except Exception as e:
    print(f"❌ Error loading application: {e}")
    # Create a simple error app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/')
    def error():
        return f"Error loading application: {str(e)}", 500
    
    application = error_app 