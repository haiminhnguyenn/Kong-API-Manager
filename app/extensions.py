from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

engine = create_engine("postgresql+psycopg2://postgres:26032003@localhost:5432/kong_api_manager_db")
Session = sessionmaker(engine)