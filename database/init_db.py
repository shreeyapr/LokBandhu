# database/init_db.py

import os
import sys

# Add the parent directory (LokBandhu) to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from config import Config  # <-- New: Import Config to get the base directory
from models.db_models import Complaint, Service, User

# Create and configure the app
app = create_app()

def initialize_database():
    with app.app_context():
        
        # --- FIX: Ensure the 'instance' folder exists ---
        # 1. Get the base directory path from config
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        # 2. Construct the full path to the instance folder
        instance_dir = os.path.join(basedir, 'instance')
        
        # 3. Create the directory if it doesn't exist (robust way)
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, exist_ok=True)
            print(f"Created directory: {instance_dir}")
        # ------------------------------------------------
        
        # Ensure all tables are created
        db.create_all() # This will now write to the newly created directory

        # Check if an admin user already exists
        admin_email = 'admin@lokbandhu.gov'
        if User.query.filter_by(email=admin_email).first() is None:
            # Create a default Admin user
            admin_user = User(name='System Admin', email=admin_email, phone='9999900000', role='Admin')
            admin_user.set_password('adminpassword') 
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"Default Admin User created: Email: {admin_email}, Password: adminpassword")
        else:
            print("Admin user already exists.")

        print("Database initialization complete.")

if __name__ == '__main__':
    initialize_database()