from flask import Blueprint

plugins_bp = Blueprint("plugins_bp", __name__)

from app.plugins import routes