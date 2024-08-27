from app import celery
from app.extensions import db
from flask import current_app as app
from app.models import ServiceConfiguration, RouteConfiguration
from sqlalchemy import or_
import requests
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def create_kong_gw_route(service_identifier, data):
    url = f"{app.config['KONG_ADMIN_URL']}/services/{service_identifier}/routes"
    try:
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            
            new_route = RouteConfiguration(
                id=response_data.get("id"),
                paths=response_data.get("paths"),
                methods=response_data.get("methods"),
                sources=response_data.get("sources"),
                destinations=response_data.get("destinations"),
                name=response_data.get("name"),
                headers=response_data.get("headers"),
                hosts=response_data.get("hosts"),
                preserve_host=response_data.get("preserve_host"),
                regex_priority=response_data.get("regex_priority"),
                snis=response_data.get("snis"),
                https_redirect_status_code=response_data.get("https_redirect_status_code"),
                tags=response_data.get("tags"),
                protocols=response_data.get("protocols"),
                path_handling=response_data.get("path_handling"),
                response_buffering=response_data.get("response_buffering"),
                strip_path=response_data.get("strip_path"),
                request_buffering=response_data.get("request_buffering"),
                created_at=response_data.get("created_at"),
                updated_at=response_data.get("updated_at"),
                service_id=response_data["service"].get("id") 
            )

            db.session.add(new_route)
            
            service = db.session.query(ServiceConfiguration).get(new_route.service_id)
            new_route.service = service
            service.routes.append(new_route)
            
            db.session.commit()
            logger.info(f"Route created successfully: {new_route.id}")
        else:
            logger.error(f"Failed to create route. Status code: {response.status_code}, Response: {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        

@celery.task
def update_kong_gw_route(route_identifier, data):
    url = f"{app.config['KONG_ADMIN_URL']}/routes/{route_identifier}"
    try:
        response = requests.patch(url, json=data, timeout=300)
        
        if response.status_code == 200:
            route_to_update = db.session.execute(
                db.select(RouteConfiguration).where(
                    or_(
                        RouteConfiguration.id == route_identifier,
                        RouteConfiguration.name == route_identifier
                    )
                )
            ).scalar()
            
            route_to_update.refresh_updated_at(response.json().get("updated_at"))
            for key, value in data.items():
                setattr(route_to_update, key, value)
            
            service_has_updated_route = db.session.query(ServiceConfiguration).get(route_to_update.service_id)
            for route in service_has_updated_route.routes:
                if route.id == route_to_update.id:
                    route.refresh_updated_at(route_to_update.updated_at)
                    for key, value in data.items():
                        setattr(route, key, value)

            db.session.commit()
            logger.info(f"Route updated successfully: {route_to_update.id}")
        else:
            logger.error(f"Failed to update route. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        
        
@celery.task
def delete_kong_gw_route(route_identifier):
    url = f"{app.config['KONG_ADMIN_URL']}/routes/{route_identifier}"
    try:
        response = requests.delete(url, timeout=300)
        
        if response.status_code == 204:
            route_to_delete = db.session.execute(
                db.select(RouteConfiguration).where(
                    or_(
                        RouteConfiguration.id == route_identifier,
                        RouteConfiguration.name == route_identifier
                    )
                )
            )
            
            db.session.delete(route_to_delete)
            
            service_has_deleted_route = db.session.query(ServiceConfiguration).get(route_to_delete.service_id)
            service_has_deleted_route.routes = [route for route in service_has_deleted_route.routes if route.id != route_to_delete.id]
            
            db.session.commit()
            logger.info(f"Route deleted successfully: {route_to_delete.id}")
        else:
            logger.error(f"Failed to delete route. Status code: {response.status_code}, Response: {response.text}")
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")