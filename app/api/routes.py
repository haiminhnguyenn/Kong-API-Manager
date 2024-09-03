from app.api import api
from flask import request, jsonify, current_app as app
from app.models import API
from app.extensions import db
from sqlalchemy import or_, and_
from app.async_tasks.async_api_tasks import async_create_api, async_update_api, async_delete_api


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
        
        
@api.route("/", methods=["POST"])
def create_api():
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
    
        if not data.get("url") or not data.get("path"):
            return jsonify({
                "error": "Missing required fields.",
                "message": "The required fields 'url' and 'path' must be provided."
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
        
        async_create_api.delay(data)
        
        return jsonify({
            "message": "API creation request has been submitted."
        }), 202
        
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
                
        async_update_api.delay(api_identifier, data)
        
        return jsonify({
            "message": "API update request has been submitted."
        }), 202
        
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
            })
            
        async_delete_api.delay(api_identifier)
        
        return jsonify({
            "message": "API deletion request has been submitted."
        }), 202
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500  