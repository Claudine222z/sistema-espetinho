#!/usr/bin/env python3
"""
WSGI entry point for Sistema Espetinho
This file is used by Gunicorn in production
"""

import os
from app import app, db

# Initialize database and create admin user
with app.app_context():
    # Create database tables if they don't exist
    db.create_all()
    
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

# Export the app for Gunicorn
application = app 