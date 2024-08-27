from flask import Blueprint

routes_bp = Blueprint("routes_bp", __name__)

from app.routes import routes