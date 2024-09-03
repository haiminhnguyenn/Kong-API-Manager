from app import celery
from app.extensions import db
from flask import current_app as app
from app.models import API
from sqlalchemy import or_
import requests
import logging
import time


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def async_create_api(data):
    try:
        new_api = API(
            name=data.get("name") if data.get("name") else None,
            url=data.get("url"),
            path=data.get("path"),
            headers=data.get("headers") if data.get("headers") else None,
            methods=data.get("methods") if data.get("methods") else None
        )
        
        create_service_url = f"{app.config['KONG_ADMIN_URL']}/services"
        create_service_data = {
            "url": data.get("url"),
            **({"name": data.get("name")} if data.get("name") else {})
        }
        
        create_service_response = requests.post(create_service_url, json=create_service_data, timeout=300)
        
        if create_service_response.status_code == 201:
            new_api.kong_service_id = create_service_response.json().get("id")
            logger.info(f"Service created successfully in Kong Gateway with ID: {new_api.kong_service_id}")
        else:
            logger.error(f"Failed to create service in Kong Gateway. Status code: {create_service_response.status_code}, Response: {create_service_response.text}")
            return
            
        create_route_url = f"{app.config['KONG_ADMIN_URL']}/services/{new_api.kong_service_id}/routes"
        create_route_data = {
            "paths": [data.get("path")],
            **({"headers": data.get("headers")} if data.get("headers") else {}),
            **({"methods": data.get("methods")} if data.get("methods") else {})
        }
        
        create_route_response = requests.post(create_route_url, json=create_route_data, timeout=300)
        
        if create_route_response.status_code == 201:
            new_api.kong_route_id = create_route_response.json().get("id")
            logger.info(f"Route created successfully in Kong Gateway with ID: {new_api.kong_route_id}")
        else:
            logger.error(f"Failed to create route in Kong Gateway. Status code: {create_route_response.status_code}, Response: {create_route_response.text}"
                         "Initiating service deletion...")
            
            delete_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{new_api.kong_service_id}"
            
            max_retries = 5
            attempt = 0
            
            while attempt < max_retries:
                delete_service_response = requests.delete(delete_service_url, timeout=300)
                
                if delete_service_response.status_code == 204:
                    logger.info(f"Service with ID: {new_api.kong_service_id} successfully deleted from Kong Gateway")
                    return
                elif delete_service_response.status_code >= 400:
                    logger.error(f"Failed to delete service in Kong Gateway. Status code: {delete_service_response.status_code}, Response: {delete_service_response.text}")
                    return
                
                attempt += 1
                time.sleep(2 ** attempt) 
            
            if attempt == max_retries:
                logger.error("Failed to delete service in Kong Gateway after maximum retries")
                
            return
        
        db.session.add(new_api)
        db.session.commit()
        logger.info(f"API created successfully with ID: {new_api.id}")
        
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()


@celery.task
def async_update_api(identifier, data):
    try:
        api_to_update = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == identifier,
                    API.name == identifier
                )
            )
        ).scalar()
        
        update_service_data = {
            field: data.get(field) for field in ["name", "url", "enabled"] 
            if data.get(field)
        }
        
        if update_service_data:
            original_service_data = {
                "name": api_to_update.name,
                "url": api_to_update.url,
                "enabled": api_to_update.enabled
            }
            
            update_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{api_to_update.kong_service_id}"
            update_service_response = requests.patch(update_service_url, json=update_service_data, timeout=300)
            
            if update_service_response.status_code == 200:
                for key, value in update_service_data.items():
                    setattr(api_to_update, key, value)
                    
                logger.info(f"Service with ID: {api_to_update.kong_service_id} successfully updated from Kong Gateway")
            else:
                logger.error(f"Failed to update service in Kong Gateway. Status code: {update_service_response.status_code}, Response: {update_service_response.text}")
                return
                
        update_route_data = {
            field: data.get(field) for field in ["path", "headers", "methods"] 
            if data.get(field)
        }
        
        if update_route_data:
            update_route_url = f"{app.config['KONG_ADMIN_URL']}/routes/{api_to_update.kong_route_id}"
            update_route_response = requests.patch(update_route_url, json=update_route_data, timeout=300)
            
            if update_route_response.status_code == 200:
                for key, value in update_route_data.items():
                    setattr(api_to_update, key, value)
                    
                logger.info(f"Route with ID: {api_to_update.kong_route_id} successfully updated from Kong Gateway")
            else:
                logger.error(f"Failed to update route in Kong Gateway. Status code: {update_route_response.status_code}, Response: {update_route_response.text}"
                             f"Initiating to rollback service in Kong Gateway...")
                
                max_retries = 5
                attempt = 0
                
                while attempt < max_retries:
                    rollback_service_response = requests.patch(update_service_url, json=original_service_data, timeout=300)
                    
                    if rollback_service_response.status_code == 200:
                        logger.info(f"Rolled back service with ID: {api_to_update.kong_service_id} due to route update failure")
                        return
                    elif rollback_service_response.status_code >= 400:
                        logger.error(f"Failed to rollback service in Kong Gateway. Status code: {rollback_service_response.status_code}, Response: {rollback_service_response.text}")
                        return
                    
                    attempt += 1
                    time.sleep(2 ** attempt) 
                
                if attempt == max_retries:
                    logger.error("Failed to rollback service in Kong Gateway after maximum retries")
                    
                return
            
        db.session.commit()
        logger.info(f"API updated successfully with ID: {api_to_update.id}")
                    
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()
        
        
@celery.task
def async_delete_api(identifier):
    try:
        api_to_delete = db.session.execute( 
            db.select(API).where(
                or_(
                    API.id == identifier,
                    API.name == identifier
                )
            )
        ).scalar()
        
        delete_route_url = f"{app.config['KONG_ADMIN_URL']}/routes/{api_to_delete.kong_route_id}"
        delete_route_response = requests.delete(delete_route_url, timeout=300)
        
        if delete_route_response.status_code == 204:
            logger.info(f"Route with ID: {api_to_delete.kong_route_id} successfully deleted from Kong Gateway")
        else:
            logger.info(f"Failed to delete route in Kong Gateway. Status code: {delete_route_response.status_code}, Response: {delete_route_response.text}")
            return
        
        delete_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{api_to_delete.kong_service_id}"
        delete_service_response = requests.delete(delete_service_url, timeout=300)
        
        if delete_service_response.status_code == 204:
            logger.info(f"Service with ID: {api_to_delete.kong_service_id} successfully deleted from Kong Gateway")
        else:
            logger.error(f"Failed to delete service in Kong Gateway. Status code: {delete_service_response.status_code}, Response: {delete_service_response.text}"
                         f"Initiating to rollback route in Kong Gateway...")
            
            rollback_route_url = f"{app.config['KONG_ADMIN_URL']}/services/{api_to_delete.kong_service_id}/routes"
            rollback_route_data = {
                "paths": [api_to_delete.path],
                "headers": api_to_delete.headers,
                "methods": api_to_delete.methods
            }
            
            max_retries = 5
            attempt = 0
                
            while attempt < max_retries:
                rollback_route_response = requests.post(rollback_route_url, json=rollback_route_data, timeout=300)
                    
                if rollback_route_response.status_code == 201:
                    api_to_delete.kong_route_id = rollback_route_response.json().get("id")
                    db.session.commit()
                    logger.info(f"Rolled back route with ID: {api_to_delete.kong_route_id} after service delete failure")
                    return
                elif rollback_route_response.status_code >= 400:
                    logger.error(f"Failed to rollback route in Kong Gateway. Status code: {rollback_route_response.status_code}, Response: {rollback_route_response.text}")
                    return
                    
                attempt += 1
                time.sleep(2 ** attempt) 
                
            if attempt == max_retries:
                logger.error("Failed to rollback route in Kong Gateway after maximum retries")
                    
            return
        
        db.session.delete(api_to_delete)
        db.session.commit()
        
    except requests.RequestException as e:
        db.session.rollback()
        logger.error(f"Request failed: {e}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        
    finally:
        db.session.close()      