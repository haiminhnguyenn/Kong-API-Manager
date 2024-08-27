from app.routes import routes_bp
from flask import request, jsonify, current_app as app
from app.route_async_tasks import create_kong_gw_route
from app.models.service import ServiceConfiguration
from app.models.route import RouteConfiguration
from app.extensions import db
from sqlalchemy import or_


@routes_bp.route("/services/<service_identifier>/routes", methods=["POST"])
def create_route(service_identifier):
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
        )
        
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