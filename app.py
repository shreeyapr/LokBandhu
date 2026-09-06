# app.py

from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy

from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions (BINDING THE DB TO THE APP)
    db.init_app(app)
    login_manager.init_app(app)
    # FIX 1: Change login_view to use the blueprint name 'auth'
    login_manager.login_view = 'auth.login' 

    # --- DELETE THE LINE BELOW! ---
    # from models.db_models import User, Complaint, Service 
    # ^^^ Removing this prevents the early database binding error.
    
    # Optional: Set the user_loader function for Flask-Login
    # FIX 2: We wrap the user_loader logic in app_context for robustness
    with app.app_context():
        from models.db_models import User  # Import here for the user_loader
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    # --- REGISTER BLUEPRINTS (ROUTES) ---
    from routes.admin_routes import admin_bp
    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp
    from routes.citizen_routes import citizen_bp 
    from routes.lang_routes import lang_bp
  
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(lang_bp) 

    @app.route('/')
    def index():
        # If logged in, redirect to respective dashboard
        if current_user.is_authenticated:
            if current_user.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('citizen.dashboard'))
        
        # If not logged in, show the landing page
        return render_template('index.html')
    
    @app.route('/about')
    def about():
    # Looks directly in the root of the /templates folder
        return render_template('about.html')

    @app.route('/services-hub')
    def services_landing():
        # Looks directly in the root of the /templates folder
        return render_template('services_landing.html')

    @app.route('/contact')
    def contact():
        # Looks directly in the root of the /templates folder
        return render_template('contact.html')
    
    @app.context_processor
    def inject_translations():
        from flask import session
        from utils.translations import get_translation, SUPPORTED_LANGUAGES
        lang = session.get('lang', 'en')
        return dict(
            t=get_translation(lang),
            current_lang=lang,
            supported_languages=SUPPORTED_LANGUAGES
        )

    return app



if __name__ == '__main__':
    app = create_app()
    # Create tables only if app is being run directly
    with app.app_context():
        # Import models here so db.create_all() sees them
        from models.db_models import Complaint, Service, User
        db.create_all()
    app.run(debug=True)