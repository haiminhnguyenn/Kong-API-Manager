from app import celery
from app.extensions import db
from flask import current_app as app
from app.models import ServiceConfiguration, RouteConfiguration, PluginConfiguration
from sqlalchemy import or_
import requests
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def create_kong_gw_plugin(data):
    url = f"{app.config['KONG_ADMIN_URL']}/plugins"
    try:
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            
            new_plugin = PluginConfiguration(
                id=response_data.get("id"),
                enable=response_data.get("enable"),
                protocols=response_data.get("protocols"),
                ordering=response_data.get("ordering"),
                consumer_id=response_data["consumer"].get("id"),
                consumer_group_id=response_data["consumer_group"].get("id"),
                instance_name=response_data.get("instance_name"),
                config=response_data.get("config"),
                name=response_data.get("name"),
                created_at=response_data.get("created_at"),
                updated_at=response_data.get("updated_at"),
                tags=response_data.get("tags"),
                service_id=response_data["service"].get("id"),
                route_id=response_data["route"].get("id")
            )
            
            db.session.add(new_plugin)
            db.session.commit()
            logger.info(f"Plugin created successfully: {new_plugin.id}")
        else:
            logger.error(f"Failed to create plugin. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    

@celery.task
def create_kong_gw_plugin_for_service(service_identifier, data):
    url = f"{app.config['KONG_ADMIN_URL']}/services/{service_identifier}/plugins"
    try:
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            
            new_plugin = PluginConfiguration(
                id=response_data.get("id"),
                enable=response_data.get("enable"),
                protocols=response_data.get("protocols"),
                ordering=response_data.get("ordering"),
                consumer_id=response_data["consumer"].get("id"),
                consumer_group_id=response_data["consumer_group"].get("id"),
                instance_name=response_data.get("instance_name"),
                config=response_data.get("config"),
                name=response_data.get("name"),
                created_at=response_data.get("created_at"),
                updated_at=response_data.get("updated_at"),
                tags=response_data.get("tags"),
                service_id=response_data["service"].get("id"),
                route_id=response_data["route"].get("id")
            )
            
            db.session.add(new_plugin)
            
            service = db.session.query(ServiceConfiguration).get(new_plugin.service_id)
            service.plugins.append(new_plugin)
            new_plugin.service = service
            
            db.session.commit()
            logger.info(f"Plugin created successfully: {new_plugin.id}")
        else:
            logger.error(f"Failed to create plugin. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        
        
@celery.task
def create_kong_gw_plugin_for_route(route_identifier, data):
    url = f"{app.config['KONG_ADMIN_URL']}/routes/{route_identifier}/plugins"
    try:
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            
            new_plugin = PluginConfiguration(
                id=response_data.get("id"),
                enable=response_data.get("enable"),
                protocols=response_data.get("protocols"),
                ordering=response_data.get("ordering"),
                consumer_id=response_data["consumer"].get("id"),
                consumer_group_id=response_data["consumer_group"].get("id"),
                instance_name=response_data.get("instance_name"),
                config=response_data.get("config"),
                name=response_data.get("name"),
                created_at=response_data.get("created_at"),
                updated_at=response_data.get("updated_at"),
                tags=response_data.get("tags"),
                service_id=response_data["service"].get("id"),
                route_id=response_data["route"].get("id")
            )
            
            db.session.add(new_plugin)
            
            route = db.session.query(RouteConfiguration).get(new_plugin.route_id)
            route.plugins.append(new_plugin)
            new_plugin.route = route
            
            db.session.commit()
            logger.info(f"Plugin created successfully: {new_plugin.id}")
        else:
            logger.error(f"Failed to create plugin. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        
        
@celery.task
def update_kong_gw_plugin(plugin_identifier, data):
    url = f"{app.config['KONG_ADMIN_URL']}/plugins/{plugin_identifier}"
    try:
        response = requests.patch(url, json=data, timeout=300)
        
        if response.status_code == 200:
            plugin_to_update = db.session.execute(
                db.select(PluginConfiguration).where(
                    or_(
                        PluginConfiguration.id == plugin_identifier,
                        PluginConfiguration.instance_name == plugin_identifier
                    )
                )
            ).scalar()
            
            plugin_to_update.refresh_updated_at(response.json().get("updated_at"))
            for key, value in data.items():
                setattr(plugin_to_update, key, value)
            
            if plugin_to_update.service_id is not None:
                service_has_updated_plugin = db.session.query(ServiceConfiguration).get(plugin_to_update.service_id)
                for plugin in service_has_updated_plugin.plugins:
                    if plugin.id == plugin_to_update.id:
                        plugin.refresh_updated_at(plugin_to_update.updated_at)
                        for key, value in data.items():
                            setattr(plugin, key, value)
                            
            if plugin_to_update.route_id is not None:
                route_has_updated_plugin = db.session.query(RouteConfiguration).get(plugin_to_update.route_id)
                for plugin in route_has_updated_plugin.plugins:
                    if plugin.id == plugin_to_update.id:
                        plugin.refresh_updated_at(plugin_to_update.updated_at)
                        for key, value in data.items():
                            setattr(plugin, key, value)

            db.session.commit()
            logger.info(f"Plugin updated successfully: {plugin_to_update.id}")
        else:
            logger.error(f"Failed to update plugin. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        
        
@celery.task
def delete_kong_gw_plugin(plugin_identifier):
    url = f"{app.config['KONG_ADMIN_URL']}/plugins/{plugin_identifier}"
    try:
        response = requests.delete(url, timeout=300)
        
        if response.status_code == 204:
            plugin_to_delete = db.session.execute(
                db.select(PluginConfiguration).where(
                    or_(
                        PluginConfiguration.id == plugin_identifier,
                        PluginConfiguration.instance_name == plugin_identifier
                    )
                )
            ).scalar()
            
            db.session.delete(plugin_to_delete)
            
            if plugin_to_delete.service_id is not None:
                service_has_deleted_plugin = db.session.query(ServiceConfiguration).get(plugin_to_delete.service_id)
                service_has_deleted_plugin.plugins = [plugin for plugin in service_has_deleted_plugin.plugins if plugin.id != plugin_to_delete.id]
                
            if plugin_to_delete.route_id is not None:
                route_has_deleted_plugin = db.session.query(RouteConfiguration).get(plugin_to_delete.route_id)
                route_has_deleted_plugin.plugins = [plugin for plugin in route_has_deleted_plugin.plugins if plugin.id != plugin_to_delete.id]
            
            db.session.commit()
            logger.info(f"Plugin deleted successfully: {plugin_to_delete.id}")
        else:
            logger.error(f"Failed to delete plugin. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")