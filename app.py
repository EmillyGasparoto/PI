import os
import logging

from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_login import LoginManager, current_user
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Create the app first
app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')  
app.jinja_env.globals['now'] = datetime.utcnow  
app.secret_key = os.environ.get("SESSION_SECRET", "my-super-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Initialize extensions
db = SQLAlchemy(model_class=Base)
ma = Marshmallow()
jwt = JWTManager()
login_manager = LoginManager()

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///clinic.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("SESSION_SECRET", "my-super-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour

# Initialize extensions with app
db.init_app(app)
ma.init_app(app)
jwt.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
# Set login view after initializing with app
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

with app.app_context():
    # Import models for SQLAlchemy to detect them
    import models  # noqa: F401
    
    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.patients import patients_bp
    from routes.doctors import doctors_bp
    from routes.appointments import appointments_bp
    from routes.medical_records import medical_records_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(medical_records_bp)
    
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Root route to display the homepage
@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)