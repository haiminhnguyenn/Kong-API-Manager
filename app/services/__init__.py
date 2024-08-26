from flask import Blueprint

services = Blueprint("services", __name__)

from app.services import routes