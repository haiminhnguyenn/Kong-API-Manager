from app.services import services
from flask import request, jsonify, current_app as app
from app.tasks import create_kong_gw_service
from app.models.service import ServiceConfiguration
from app.extensions import db


@services.route("/", methods=["POST"])
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
            "data": filtered_data,
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
        

@services.route("/")
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


@services.route("/<identifier>")
def get_service(identifier):
    try:
        service = db.session.execute(
            db.select(ServiceConfiguration)
            .where(ServiceConfiguration.id == identifier or ServiceConfiguration.name == identifier)
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
        

@services.route("/<identifier>", methods=["PATCH"])
def update_service(identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        service_to_update = db.session.execute(
            db.select(ServiceConfiguration)
            .where(ServiceConfiguration.id == identifier or ServiceConfiguration.name == identifier)
        ).scalar()
        
        if service_to_update is None:
            return jsonify({
                "error": "Service not found.",
                "message": "No service found with the provided identifier."
            }), 404
        
        # ignored_fields = set()
        
        # for key, value in data.items():
        #     if key in app.config["SERVICE_CONFIG_FIELDS"]:
        #         setattr(service_to_update, key, value)
        #     else:
        #         ignored_fields.add(key)
        
        # db.session.commit()
        # return jsonify({
        #     "status": "success",
        #     "ignored_fields": list(ignored_fields),
        #     "updated_service": service_to_update.to_dict()
        # }), 200

    
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