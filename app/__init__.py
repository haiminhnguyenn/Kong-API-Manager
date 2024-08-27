from flask import Flask
from config import Config
from app.extensions import db
from celery import Celery


celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    celery.conf.update(app.config)
    
    from app.services import services_bp
    app.register_blueprint(services_bp, url_prefix="/services")
    
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)
    
    return app