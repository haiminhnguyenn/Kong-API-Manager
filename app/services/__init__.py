from flask import Blueprint

services_bp = Blueprint("services_bp", __name__)

from app.services import routes