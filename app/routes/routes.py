from app.routes import routes_bp
from flask import request, jsonify, current_app as app
from app.async_tasks.route_async_tasks import create_kong_gw_route, create_kong_gw_route_for_service, update_kong_gw_route, delete_kong_gw_route
from app.models import ServiceConfiguration, RouteConfiguration
from app.extensions import db
from sqlalchemy import or_


@routes_bp.route("/routes", methods=["POST"])
def create_route():
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
    
        if "protocols" not in data or any(protocol in ["http", "https"] for protocol in data.get("protocols", [])):
            if not data.get("methods") and not data.get("hosts") and not data.get("headers") and not data.get("paths") and not data.get("snis"):
                return jsonify({
                    "error": "Missing required field.",
                    "message": "Must set one of 'methods', 'hosts', 'headers', 'snis'(for 'https'), 'paths' when 'protocols' is 'http' or 'https'."
                }), 400
                
        if data.get("name") is not None:
            route_name = data.get("name")
            existed_route = db.session.execute(
                db.select(RouteConfiguration)
                .where(RouteConfiguration.name == route_name)
            ).scalar()
            
            if existed_route:
                return jsonify({
                    "error": f"UNIQUE violation detected on 'name=\"{route_name}\"'",
                    "message": f"A route with the name '{route_name}' already exists."
                }), 409
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["ROUTE_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_route.delay(filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Route creation request has been submitted."
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


@routes_bp.route("/services/<service_identifier>/routes", methods=["POST"])
def create_route_for_service(service_identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        service = db.session.execute(
            db.select(ServiceConfiguration).where(
                or_(
                    ServiceConfiguration.id == service_identifier,
                    ServiceConfiguration.name == service_identifier
                )
            )
        ).scalar()
        
        if service is None:
            return jsonify({
                "message": "Not found."
            }), 404
        
        if "protocols" not in data or any(protocol in ["http", "https"] for protocol in data.get("protocols", [])):
            if not data.get("methods") and not data.get("hosts") and not data.get("headers") and not data.get("paths") and not data.get("snis"):
                return jsonify({
                    "error": "Missing required field.",
                    "message": "Must set one of 'methods', 'hosts', 'headers', 'snis'(for 'https'), 'paths' when 'protocols' is 'http' or 'https'."
                }), 400
                
        if data.get("name") is not None:
            route_name = data.get("name")
            existed_route = db.session.execute(
                db.select(RouteConfiguration)
                .where(RouteConfiguration.name == route_name)
            ).scalar()
            
            if existed_route:
                return jsonify({
                    "error": f"UNIQUE violation detected on 'name=\"{route_name}\"'",
                    "message": f"A route with the name '{route_name}' already exists."
                }), 409
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["ROUTE_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_route_for_service.delay(service_identifier, filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Route creation request has been submitted."
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


@routes_bp.route("/routes")
def get_all_routes():
    try:
        routes_list = RouteConfiguration.query.all()
        routes_data = [route.to_dict() for route in routes_list]

        return jsonify({
            "routes": routes_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        

@routes_bp.route("/services/<service_identifier>/routes")
def get_all_routes_for_service(service_identifier):
    try:
        service = db.session.execute(
            db.select(ServiceConfiguration).where(
                or_(
                    ServiceConfiguration.id == service_identifier,
                    ServiceConfiguration.name == service_identifier
                )
            )
        ).scalar()
        
        if service is None:
            return jsonify({
                "message": "Service not found."
            }), 404
        
        routes_list = service.routes
        routes_data = [route.to_dict() for route in routes_list]
        
        return jsonify({
                "service_id": service.id,
                "routes": routes_data
            }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        

@routes_bp.route("/routes/<route_identifier>")
def get_route(route_identifier):
    try:
        route = db.session.execute(
            db.select(RouteConfiguration).where(
                or_(
                    RouteConfiguration.id == route_identifier,
                    RouteConfiguration.name == route_identifier
                )
            )
        ).scalar()
        
        if route is None:
            return jsonify({
                "error": "Route not found."
            }), 404
        
        route_data = route.to_dict()
        
        return jsonify({
                "route": route_data
            }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
    
 
@routes_bp.route("/routes/<route_identifier>", methods=["PATCH"])
def update_route(route_identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        route_to_update = db.session.execute(
            db.select(RouteConfiguration).where(
                or_(
                    RouteConfiguration.id == route_identifier,
                    RouteConfiguration.name == route_identifier
                )
            )
        ).scalar()
        
        if route_to_update is None:
            return jsonify({
                "error": "Route not found.",
                "message": "No route found with the provided identifier."
            }), 404
            
        if data.get("name") is not None:
            new_route_name = data.get("name")
            conflict_route = db.session.execute(
                db.select(RouteConfiguration)
                .where(RouteConfiguration.name == new_route_name)
            ).scalar()
            
            if conflict_route:
                return jsonify({
                    "error": f"UNIQUE violation detected on 'name=\"{new_route_name}\"'",
                    "message": f"The name '{new_route_name}' conflict with an existing route."
                }), 409
            
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["ROUTE_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
                
        update_kong_gw_route.delay(route_identifier ,filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Route update request has been submitted."
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


@routes_bp.route("/routes/<route_identifier>", methods=["DELETE"])
def delete_route(route_identifier):
    try:
        route_to_delete = db.session.execute(
            db.select(RouteConfiguration).where(
                or_(
                    RouteConfiguration.id == route_identifier,
                    RouteConfiguration.name == route_identifier
                )
            )
        )
        
        if route_to_delete is None:
            return jsonify({
                "error": "Route not found.",
                "message": "No route found with the provided identifier."
            }), 404
        
        delete_kong_gw_route.delay(route_identifier)
        
        return jsonify({
            "message": "Route deletion request has been submitted."
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500