from app import celery
from app.extensions import db
from flask import current_app as app
from app.models.service import ServiceConfiguration
from sqlalchemy import or_
import requests
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@celery.task
def create_kong_gw_route(data):
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
                created_at=response_data["created_at"],
                updated_at=response_data["updated_at"],
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