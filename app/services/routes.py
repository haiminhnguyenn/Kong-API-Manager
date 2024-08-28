from app.services import services_bp
from flask import request, jsonify, current_app as app
from app.async_tasks.service_async_tasks import create_kong_gw_service, update_kong_gw_service, delete_kong_gw_service
from app.models import ServiceConfiguration
from app.extensions import db
from sqlalchemy import or_


@services_bp.route("/", methods=["POST"])
def create_service():
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
    
        if data.get("host") is None and data.get("url") is None:
            return jsonify({
                "error": "Missing required field.",
                "message": "One of the required fields 'host' or 'url' must be provided."
            }), 400
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["SERVICE_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_service.delay(filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Service creation request has been submitted."
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid data.",
            "message": str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        

@services_bp.route("/")
def get_all_services():
    try:
        services_list = ServiceConfiguration.query.all()
        services_data = [service.to_dict() for service in services_list]

        return jsonify({
            "services": services_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500


@services_bp.route("/<identifier>")
def get_service(identifier):
    try:
        service = db.session.execute(
            db.select(ServiceConfiguration).where(
                or_(
                    ServiceConfiguration.id == identifier,
                    ServiceConfiguration.name == identifier
                )   
            )
        ).scalar()
        
        if service is None:
            return jsonify({
                "error": "Service not found."
            }), 404
            
        service_data = service.to_dict()
        return jsonify({
            "service": service_data
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500 
        

@services_bp.route("/<identifier>", methods=["PATCH"])
def update_service(identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        service_to_update = db.session.execute(
            db.select(ServiceConfiguration).where(
                or_(
                    ServiceConfiguration.id == identifier,
                    ServiceConfiguration.name == identifier
                )
            )
        ).scalar()
        
        if service_to_update is None:
            return jsonify({
                "error": "Service not found.",
                "message": "No service found with the provided identifier."
            }), 404
            
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["SERVICE_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
                
        update_kong_gw_service.delay(identifier ,filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Service update request has been submitted."
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid data.",
            "message": str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
       

@services_bp.route("/<identifier>", methods=["DELETE"])
def delete_service(identifier):
    try:
        service_to_delete = db.session.execute(
            db.select(ServiceConfiguration).where(
                or_(
                    ServiceConfiguration.id == identifier,
                    ServiceConfiguration.name == identifier
                )
            )
        ).scalar()
        
        if service_to_delete is None:
            return jsonify({
                "error": "Service not found.",
                "message": "No service found with the provided identifier."
            }), 404
            
        if service_to_delete.routes:
            return jsonify({
                "error": "An existing 'routes' entity references this 'services' entity"
            }), 400
        
        delete_kong_gw_service.delay(identifier)
        
        return jsonify({
            "message": "Service deletion request has been submitted."
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500