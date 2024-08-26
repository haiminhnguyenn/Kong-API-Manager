from flask_sqlalchemy import SQLAlchemy
from app.models.base import Base

db = SQLAlchemy(model_class=Base)