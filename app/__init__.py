from flask import Flask
from config import Config
from app.extensions import db
from celery import Celery
from app import events


celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    celery.conf.update(app.config)
    
    from app.api import api as api_bp
    app.register_blueprint(api_bp, url_prefix="apis")
    
    from app.plugin import plugin as plugin_bp
    app.register_blueprint(plugin_bp)
    
    return app