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
def create_kong_gw_service(data):
    url = f"{app.config['KONG_ADMIN_URL']}/services"
    try:
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            
            new_service = ServiceConfiguration(
                id=response_data.get("id"),
                host=response_data.get("host"),
                name=response_data.get("name"),
                enable=response_data.get("enable"),
                connect_timeout=response_data.get("connect_timeout"),
                read_timeout=response_data.get("read_timeout"),
                retries=response_data.get("retries"),
                protocol=response_data.get("protocol"),
                path=response_data.get("path"),
                port=response_data.get("port"),
                tags=response_data.get("tags"),
                client_certificate=response_data.get("client_certificate"),
                tls_verify=response_data.get("tls_verify"),
                created_at=response_data.get("created_at"),
                updated_at=response_data.get("updated_at"),
                tls_verify_depth=response_data.get("tls_verify_depth"),
                write_timeout=response_data.get("write_timeout"),
                ca_certificates=response_data.get("ca_certificates")
            )
            
            db.session.add(new_service)
            db.session.commit()
            logger.info(f"Service created successfully: {new_service.id}")
        else:
            logger.error(f"Failed to create service. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


@celery.task
def update_kong_gw_service(identifier ,data):
    url = f"{app.config['KONG_ADMIN_URL']}/services/{identifier}"
    try:
        response = requests.patch(url, json=data, timeout=300)
        
        if response.status_code == 200:
            service_to_update = db.session.execute(
                db.select(ServiceConfiguration).where(
                    or_(
                        ServiceConfiguration.id == identifier,
                        ServiceConfiguration.name == identifier
                    )
                )
            ).scalar()
            
            service_to_update.refresh_updated_at(response.json().get("updated_at"))
            for key, value in data.items():
                setattr(service_to_update, key, value)
            
            if service_to_update.routes:
                routes_for_updated_service = db.session.query(RouteConfiguration).filter(
                    RouteConfiguration.service_id == service_to_update.id
                ).all()
                for route in routes_for_updated_service:
                    route.service.refresh_updated_at(service_to_update.updated_at)
                    for key, value in data.items():
                        setattr(route.service, key, value)
            
            if service_to_update.plugins:
                plugins_for_updated_service = db.session.query(PluginConfiguration).filter(
                    PluginConfiguration.service_id == service_to_update.id
                ).all()
                for plugin in plugins_for_updated_service:
                    plugin.service.refresh_updated_at(service_to_update.updated_at)
                    for key, value in data.items():
                        setattr(plugin.service, key, value)

            db.session.commit()
            logger.info(f"Service updated successfully: {service_to_update.id}")
        else:
            logger.error(f"Failed to update service. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


@celery.task
def delete_kong_gw_service(identifier):
    url = f"{app.config['KONG_ADMIN_URL']}/services/{identifier}"
    try:
        response = requests.delete(url, timeout=300)
        
        if response.status_code == 204:
            service_to_delete = db.session.execute(
                db.select(ServiceConfiguration).where(
                    or_(
                        ServiceConfiguration.id == identifier,
                        ServiceConfiguration.name == identifier
                    )
                )
            ).scalar()
            
            if service_to_delete.plugins:
                plugins_to_delete = db.session.query(PluginConfiguration).filter(
                    PluginConfiguration.service_id == service_to_delete.id
                ).all()
                for plugin in plugins_to_delete:
                    db.session.delete(plugin)
                
            db.session.delete(service_to_delete)
            db.session.commit()
            logger.info(f"Service deleted successfully: {service_to_delete.id}")
        else:
            logger.error(f"Failed to delete service. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")