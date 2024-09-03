from app import celery
from app.extensions import db
from flask import current_app as app
from app.models import API, Plugin, PluginAPIConfiguration
from sqlalchemy import or_
import requests
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def async_create_plugin(api_identifier, data):
    try:
        api = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        url = f"{app.config['KONG_ADMIN_URL']}/routes/{api.kong_route_id}/plugins"
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            plugin_name = response_data.get("name")
            
            plugin = db.session.execute(
                db.select(Plugin).where(Plugin.name == plugin_name)
            ).scalar()
            
            if plugin is None:
                plugin = Plugin(name=plugin_name)
                db.session.add(plugin)

            plugin_config = PluginAPIConfiguration(
                config=response_data.get("config"),
                kong_plugin_id=response_data.get("id"),
                plugin=plugin,
                api=api
            )
        
            db.session.add(plugin_config)
            db.session.commit()

            logger.info(f"Plugin '{plugin_name}' created successfully for API with ID {api.id}")
        else:
            logger.error(f"Failed to create plugin for API with ID {api.id}. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()

            
@celery.task
def async_update_plugin(api_identifier, plugin_identifier, data):
    try:
        api = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        plugin_config_to_update = db.session.execute(
            db.select(PluginAPIConfiguration)
            .join(Plugin, Plugin.id == PluginAPIConfiguration.plugin_id)
            .where(
                PluginAPIConfiguration.api_id == api.id,
                or_(
                    Plugin.id == plugin_identifier,
                    Plugin.name == plugin_identifier
                )
            )
        ).scalar()
        
        url = f"{app.config['KONG_ADMIN_URL']}/plugins/{plugin_config_to_update.kong_plugin_id}"
        response = requests.patch(url, json=data, timeout=300)
        
        if response.status_code == 200:
            response_data = response.json()
            
            for key, value in data.items():
                setattr(plugin_config_to_update, key, value)
                
            db.session.commit()
            logger.info(f"Plugin '{plugin_config_to_update.plugin.name}' updated successfully for API with ID {api.id}")
        else:
            logger.error(f"Failed to update plugin for API with ID {api.id}. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()
        
        
@celery.task
def async_delete_plugin(api_identifier, plugin_identifier):
    try:
        api = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        plugin_config_to_delete = db.session.execute(
            db.select(PluginAPIConfiguration)
            .join(Plugin, Plugin.id == PluginAPIConfiguration.plugin_id)
            .where(
                PluginAPIConfiguration.api_id == api.id,
                or_(
                    Plugin.id == plugin_identifier,
                    Plugin.name == plugin_identifier
                )
            )
        ).scalar()
        
        plugin = plugin_config_to_delete.plugin
        
        url = f"{app.config['KONG_ADMIN_URL']}/plugins/{plugin_config_to_delete.kong_plugin_id}"
        response = requests.delete(url, timeout=300)
        
        if response.status_code == 204:
            db.session.delete(plugin_config_to_delete)
            db.session.commit()
            logger.info(f"Plugin '{plugin_config_to_delete.plugin.name}' deleted successfully for API with ID {api.id}")
        else:
            logger.error(f"Failed to delete plugin for API with ID {api.id}. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()