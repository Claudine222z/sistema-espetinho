#!/usr/bin/env python3
"""
WSGI entry point for Sistema Espetinho
This file is used by Gunicorn in production
"""

import os
from app import app, db

# Configure for production
if __name__ == "__main__":
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
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 