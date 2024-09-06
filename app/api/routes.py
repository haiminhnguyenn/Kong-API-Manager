from flask import request, jsonify, current_app as app
from sqlalchemy import or_, and_

from app.extensions import db
from app.models import API
from app.api import api
from app.kong_client.api_client import (
    create_service_in_kong, create_route_in_kong, 
    update_service_in_kong, update_route_in_kong, 
    delete_service_in_kong, delete_route_in_kong
)
from app.async_tasks import (
    rollback_for_api_creation_failure, 
    rollback_for_api_update_failure, 
    rollback_for_api_delete_failure
)


@api.route("/")
def list_apis():
    try:
        apis_list = API.query.all()
        apis_data = [api.to_dict() for api in apis_list]

        return jsonify({
            "APIs": apis_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
       
        
@api.route("/<api_identifier>")
def get_api(api_identifier):
    try:
        api = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )   
            )
        ).scalar()
        
        if api is None:
            return jsonify({
                "error": "Not found."
            }), 404
            
        api_data = api.to_dict()
        return jsonify({
            "API": api_data
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
    finally:
        db.session.close()
        
        
@api.route("/", methods=["POST"])
def create_api():
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        required_fields = ["url", "path"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields.",
                "message": f"The following required fields are missing: {', '.join(missing_fields)}."
            }), 400
        
        unknown_fields = {
            field: "unknown field" for field in data.keys()
            if field not in app.config["ALLOW_FIELDS_FOR_CREATE_API"]
        }
                
        if unknown_fields:
            return jsonify({
                "error": "schema violation",
                "fields": unknown_fields
            }), 400
            
        for field in ["name", "url", "path"]:
            value = data.get(field)
            if value:
                existed_api = db.session.execute(
                    db.select(API).where(getattr(API, field) == value)
                ).scalar()
                
                if existed_api:
                    return jsonify({
                        "error": f"UNIQUE violation detected on '{field}=\"{value}\"'",
                        "message": f"An API with the {field} '{value}' already exists."
                    }), 409
        
        new_api = API(
            name=data.get("name") if data.get("name") else None,
            url=data.get("url"),
            path=data.get("path"),
            headers=data.get("headers") if data.get("headers") else None,
            methods=data.get("methods") if data.get("methods") else None
        )
        
        create_service_data = {
            "url": data.get("url"),
            **({"name": data.get("name")} if data.get("name") else {})
        }
        
        new_api.kong_service_id, service_error = create_service_in_kong(create_service_data)
        
        if service_error:
            return jsonify({
                "error": "Service creation failed.",
                "message": service_error
            }), 500
        
        create_route_data = {
            "paths": [data.get("path")],
            **({"headers": data.get("headers")} if data.get("headers") else {}),
            **({"methods": data.get("methods")} if data.get("methods") else {})
        }
        
        new_api.kong_route_id, route_error = create_route_in_kong(new_api.kong_service_id, create_route_data)
        
        if route_error:
            rollback_for_api_creation_failure.delay(new_api.kong_service_id)
            return jsonify({
                "error": "Route creation failed.",
                "message": route_error
            }), 500 
        
        db.session.add(new_api)
        db.session.commit()
        return jsonify({
            "message": "API created successfully.",
            "api_id": new_api.id
        }), 201
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid data.",
            "message": str(e)
        }), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
    finally:
        db.session.close()
        
        
@api.route("/<api_identifier>", methods=["PATCH"])
def update_api(api_identifier):
    try:
        api_to_update = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        if api_to_update is None:
            return jsonify({
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
    
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        unknown_fields = {
            field: "unknown field" for field in data.keys()
            if field not in app.config["ALLOW_FIELDS_FOR_UPDATE_API"]
        }
                
        if unknown_fields:
            return jsonify({
                "error": "schema violation",
                "fields": unknown_fields
            }), 400
                
        for field in ["name", "url", "path"]:
            value = data.get(field)
            if value:
                conflict_api = db.session.execute(
                    db.select(API).where(
                        and_(
                            getattr(API, field) == value,
                            API.id != api_to_update.id
                        )
                    )
                ).scalar()
                
                if conflict_api:
                    return jsonify({
                        "error": f"UNIQUE violation detected on '{field}=\"{value}\"'",
                        "message": f"The {field} '{value}' conflict with an existing API."
                    }), 409
                
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
            
            service_status, service_error = update_service_in_kong(api_to_update.kong_service_id, update_service_data)
            
            if service_status == "failure":
                return jsonify({
                    "error": "Service update failed.",
                    "message": service_error
                }), 500
                
            for key, value in update_service_data.items():
                setattr(api_to_update, key, value)

        update_route_data = {
            **({"paths": [data.get("path")]} if data.get("path") else {}),
            **({"headers": data.get("headers")} if data.get("headers") else {}),
            **({"methods": data.get("methods")} if data.get("methods") else {})
        }
        
        if update_route_data:
            route_status, route_error = update_route_in_kong(api_to_update.kong_route_id, update_route_data)
            
            if route_status == "success":
                for key, value in update_route_data.items():
                    if key == "paths":
                        api_to_update.path = data.get("path")
                    else:
                        setattr(api_to_update, key, value)
            else:
                if update_service_data:
                    rollback_for_api_update_failure.delay(api_to_update.kong_service_id, original_service_data)
                
                return jsonify({
                    "error": "Route update failed.",
                    "message": route_error
                }), 500
                    
        db.session.commit()
        return jsonify({
            "message": "API updated successfully."
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid data.",
            "message": str(e)
        }), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
    finally:
        db.session.close()
        
        
@api.route("/<api_identifier>", methods=["DELETE"])
def delete_api(api_identifier):
    try:
        api_to_delete = db.session.execute(
            db.select(API).where(
                or_(
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        if api_to_delete is None:
            return jsonify({
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
            
        route_status, route_error = delete_route_in_kong(api_to_delete.kong_route_id)
        
        if route_status == "failure":
            return jsonify({
                "error": "Route deletion failed.",
                "message": route_error
            }), 500
            
        service_status, service_error = delete_service_in_kong(api_to_delete.kong_service_id)
        
        if service_status == "failure":
            rollback_route_data = {
                "paths": [api_to_delete.path],
                "headers": api_to_delete.headers,
                "methods": api_to_delete.methods
            }
            
            rollback_for_api_delete_failure.delay(api_to_delete.kong_service_id, api_to_delete.id, rollback_route_data)
            return jsonify({
                "error": "Service deletion failed.",
                "message": service_error
            }), 500
        
        db.session.delete(api_to_delete)
        db.session.commit()
        return jsonify({
            "message": "API deleted successfully."
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
    finally:
        db.session.close()