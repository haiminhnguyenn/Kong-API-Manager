import logging
from flask import current_app as app
import requests
from app.extensions import db


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_plugin_in_kong(kong_service_id, data):
    try:
        url = f"{app.config['KONG_ADMIN_URL']}/services/{kong_service_id}/plugins"
        response = requests.post(url, json=data, timeout=300)
        
        if response.status_code == 201:
            response_data = response.json()
            config=response_data.get("config")
            kong_plugin_id=response_data.get("id")
            logger.info("Plugin created successfully for API")
            return config, kong_plugin_id, None
        else:
            logger.error(f"Failed to create plugin for API. Status code: {response.status_code}, Response: {response.text}")
            return None, None, response.text
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, None, str(e)

    except Exception as e:
        db.session.rollback()
        return None, None, str(e)


def update_plugin_in_kong(kong_plugin_id, data):
    try:
        url = f"{app.config['KONG_ADMIN_URL']}/plugins/{kong_plugin_id}"
        response = requests.patch(url, json=data, timeout=300)
        
        if response.status_code == 200:
            logger.info("Plugin updated successfully for API")
            return "success", None
        else:
            logger.error(f"Failed to update plugin for API. Status code: {response.status_code}, Response: {response.text}")
            return "failure", response.text
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)
        

def delete_plugin_in_kong(kong_plugin_id):
    try:
        url = f"{app.config['KONG_ADMIN_URL']}/plugins/{kong_plugin_id}"
        response = requests.delete(url, timeout=300)
        
        if response.status_code == 204:
            logger.info("Plugin deleted successfully for API")
            return "success", None
        else:
            logger.error(f"Failed to delete plugin for API. Status code: {response.status_code}, Response: {response.text}")
            return "failure", response.text
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "failure", str(e)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "failure", str(e)