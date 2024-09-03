from flask import Blueprint

plugin = Blueprint("plugin", __name__)

from app.plugin import routes