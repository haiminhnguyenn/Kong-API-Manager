import logging
from flask import current_app as app
import requests


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_service_in_kong(data):
    try:
        create_service_url = f"{app.config['KONG_ADMIN_URL']}/services"
        create_service_response = requests.post(create_service_url, json=data, timeout=300)
        
        if create_service_response.status_code == 201:
            kong_service_id = create_service_response.json().get("id")
            logger.info(f"Service created successfully in Kong Gateway with ID: {kong_service_id}")
            return kong_service_id, None
        else:
            logger.error(f"Failed to create service in Kong Gateway. Status code: {create_service_response.status_code}, Response: {create_service_response.text}")
            return None, create_service_response.text
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None, str(e)


def create_route_in_kong(kong_service_id, data):
    try: 
        create_route_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}/routes"
        create_route_response = requests.post(create_route_url, json=data, timeout=300)
        
        if create_route_response.status_code == 201:
            kong_route_id = create_route_response.json().get("id")
            logger.info(f"Route created successfully in Kong Gateway with ID: {kong_route_id}")
            return kong_route_id, None
        else:
            logger.error(f"Failed to create route in Kong Gateway. Status code: {create_route_response.status_code}, Response: {create_route_response.text}")
            return None, create_route_response.text
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None, str(e)


def update_service_in_kong(kong_service_id, data):
    try:
        update_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}"
        update_service_response = requests.patch(update_service_url, json=data, timeout=300)
            
        if update_service_response.status_code == 200:
            logger.info(f"Service with ID: {kong_service_id} successfully updated from Kong Gateway")
            return "success", None
        else:
            logger.error(f"Failed to update service in Kong Gateway. Status code: {update_service_response.status_code}, Response: {update_service_response.text}")
            return "failure", update_service_response.text
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)
                
              
def update_route_in_kong(kong_route_id, data):
    try:
        update_route_url = f"{app.config['KONG_ADMIN_URL']}/routes/{kong_route_id}"
        update_route_response = requests.patch(update_route_url, json=data, timeout=300)
            
        if update_route_response.status_code == 200:
            logger.info(f"Route with ID: {kong_route_id} successfully updated from Kong Gateway")
            return "success", None
        else:
            logger.error(f"Failed to update route in Kong Gateway. Status code: {update_route_response.status_code}, Response: {update_route_response.text}")
            return "failure", update_route_response.text  
                    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)
        
        
def delete_service_in_kong(kong_service_id):
    try:
        delete_service_url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}"
        delete_service_response = requests.delete(delete_service_url, timeout=300)
        
        if delete_service_response.status_code == 204:
            logger.info(f"Service with ID: {kong_service_id} successfully deleted from Kong Gateway")
            return "success", None
        else:
            logger.error(f"Failed to delete service in Kong Gateway. Status code: {delete_service_response.status_code}, Response: {delete_service_response.text}")
            return "failure", delete_service_response.text
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)
    
    
def delete_route_in_kong(kong_route_id):
    try:
        delete_route_url = f"{app.config['KONG_ADMIN_URL']}/routes/{kong_route_id}"
        delete_route_response = requests.delete(delete_route_url, timeout=300)
        
        if delete_route_response.status_code == 204:
            logger.info(f"Route with ID: {kong_route_id} successfully deleted from Kong Gateway")
            return "success", None
        else:
            logger.info(f"Failed to delete route in Kong Gateway. Status code: {delete_route_response.status_code}, Response: {delete_route_response.text}")
            return "failure", delete_route_response.text
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)