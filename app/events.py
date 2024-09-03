from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import Plugin
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def delete_plugin_if_empty(session: Session):
    for plugin in session.query(Plugin).all():
        if not plugin.apis:
            try:
                session.delete(plugin)
            except SQLAlchemyError as e:
                logger.error(f"Error deleting the {plugin.name} plugin: {e}")
                pass


event.listen(Session, "after_flush", delete_plugin_if_empty)