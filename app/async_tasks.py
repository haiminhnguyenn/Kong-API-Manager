import logging
import time

from flask import current_app as app
import requests

from app import celery
from app.extensions import Session
from app.models import API


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def rollback_for_api_creation_failure(kong_service_id):
    logger.info(f"Initiating rollback for service with ID: {kong_service_id}")
    delete_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}"
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1}: Rolling back service with ID: {kong_service_id}")
            delete_service_response = requests.delete(delete_service_url, timeout=300)
                
            if delete_service_response.status_code == 204:
                logger.info(f"Service with ID: {kong_service_id} successfully deleted from Kong Gateway")
                return
            elif delete_service_response.status_code >= 400:
                logger.error(f"Failed to delete service in Kong Gateway. Status code: {delete_service_response.status_code}, Response: {delete_service_response.text}")
                return

        except requests.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}: {e}")
        
        except Exception as e:
            logger.error(f"An unexpected error occurred on attempt {attempt + 1}: {e}")
        
        attempt += 1
        time.sleep(2 ** attempt)

    logger.error(f"Failed to delete service in Kong Gateway after {max_retries} attempts")
    

@celery.task
def rollback_for_api_update_failure(kong_service_id, data):
    logger.info(f"Initiating rollback for service with ID: {kong_service_id}")
    rollback_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}"
    max_retries = 5
    attempt = 0
                
    while attempt < max_retries:
        try:
            rollback_service_response = requests.patch(rollback_service_url, json=data, timeout=300)
                    
            if rollback_service_response.status_code == 200:
                logger.info(f"Rolled back service with ID: {kong_service_id} due to route update failure")
                return
            elif rollback_service_response.status_code >= 400:
                logger.error(f"Failed to rollback service in Kong Gateway. Status code: {rollback_service_response.status_code}, Response: {rollback_service_response.text}")
                return
        
        except requests.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}: {e}")
        
        except Exception as e:
            logger.error(f"An unexpected error occurred on attempt {attempt + 1}: {e}")
                    
        attempt += 1
        time.sleep(2 ** attempt) 
                     
    logger.error(f"Failed to rollback service in Kong Gateway after {max_retries} retries")
    

@celery.task
def rollback_for_api_delete_failure(kong_service_id, api_id, data):
    logger.info(f"Initiating rollback route for API with ID: {api_id}")
    rollback_route_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}/routes"
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            rollback_route_response = requests.post(rollback_route_url, json=data, timeout=300)

            if rollback_route_response.status_code == 201:
                with Session.begin() as session:
                    api_to_rollback = session.get(API, api_id)
                    api_to_rollback.kong_route_id = rollback_route_response.json().get("id")
                    logger.info(f"Rolled back route with ID: {api_to_rollback.kong_route_id} after service delete failure")
                return
            elif rollback_route_response.status_code >= 400:
                logger.error(f"Failed to rollback route in Kong Gateway. Status code: {rollback_route_response.status_code}, Response: {rollback_route_response.text}")
                return

        except requests.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}: {e}")

        except Exception as e:
            logger.error(f"An unexpected error occurred on attempt {attempt + 1}: {e}")

        attempt += 1
        time.sleep(2 ** attempt)

    logger.error(f"Failed to rollback route in Kong Gateway after {max_retries} retries")