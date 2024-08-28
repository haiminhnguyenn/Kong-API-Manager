from app.plugins import plugins_bp
from flask import request, jsonify, current_app as app
from app.async_tasks.plugin_async_tasks import create_kong_gw_plugin, create_kong_gw_plugin_for_service, create_kong_gw_plugin_for_route, update_kong_gw_plugin, delete_kong_gw_plugin
from app.models import ServiceConfiguration, RouteConfiguration, PluginConfiguration
from app.extensions import db
from sqlalchemy import or_


@plugins_bp.route("/plugins", methods=["POST"])
def create_plugin():
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
    
        if data.get("name") is None:
            return jsonify({
                "error": "Missing required field.",
                "message": "Required field 'name' must be provided."
            }), 400
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["PLUGIN_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_plugin.delay(filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Plugin creation request has been submitted."
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
        

@plugins_bp.route("/services/<service_identifier>/plugins", methods=["POST"])
def create_plugin_for_service(service_identifier):
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
        
        if data.get("name") is None:
            return jsonify({
                "error": "Missing required field.",
                "message": "Required field 'name' must be provided."
            }), 400
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["PLUGIN_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_plugin_for_service.delay(service_identifier, filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Plugin creation request has been submitted."
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
        
        
@plugins_bp.route("/routes/<route_identifier>/plugins", methods=["POST"])
def create_plugin_for_route(route_identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
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
                "message": "Not found."
            }), 404
        
        if data.get("name") is None:
            return jsonify({
                "error": "Missing required field.",
                "message": "Required field 'name' must be provided."
            }), 400
        
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["PLUGIN_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
        
        create_kong_gw_plugin_for_route.delay(route_identifier, filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Plugin creation request has been submitted."
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
        
        
@plugins_bp.route("/plugins")
def get_all_routes():
    try:
        plugins_list = PluginConfiguration.query.all()
        plugins_data = [plugin.to_dict() for plugin in plugins_list]

        return jsonify({
            "plugins": plugins_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugins_bp.route("/services/<service_identifier>/plugins")
def get_all_plugins_for_service(service_identifier):
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
        
        plugins_list = service.plugins
        plugins_data = [plugin.to_dict() for plugin in plugins_list]
        
        return jsonify({
                "service_id": service.id,
                "plugins": plugins_data
            }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugins_bp.route("/routes/<route_identifier>/plugins")
def get_all_plugins_for_route(route_identifier):
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
                "message": "Route not found."
            }), 404
        
        plugins_list = route.plugins
        plugins_data = [plugin.to_dict() for plugin in plugins_list]
        
        return jsonify({
                "route_id": route.id,
                "plugins": plugins_data
            }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugins_bp.route("/plugins/<plugin_identifier>")
def get_plugin(plugin_identifier):
    try:
        plugin = db.session.execute(
            db.select(PluginConfiguration).where(
                or_(
                    PluginConfiguration.id == plugin_identifier,
                    PluginConfiguration.instance_name == plugin_identifier
                )
            )
        ).scalar()
        
        if plugin is None:
            return jsonify({
                "error": "Plugin not found."
            }), 404
        
        plugin_data = plugin.to_dict()
        
        return jsonify({
                "plugin": plugin_data
            }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugins_bp.route("/plugins/<plugin_identifier>", methods=["PATCH"])
def update_plugin(plugin_identifier):
    try:
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        plugin_to_update = db.session.execute(
            db.select(PluginConfiguration).where(
                or_(
                    PluginConfiguration.id == plugin_identifier,
                    PluginConfiguration.instance_name == plugin_identifier
                )
            )
        ).scalar()
        
        if plugin_to_update is None:
            return jsonify({
                "error": "Plugin not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
            
        filtered_data = {}
        ignored_fields = set()
        
        for key, value in data.items():
            if key in app.config["PLUGIN_CONFIG_FIELDS"]:
                filtered_data[key] = value
            else:
                ignored_fields.add(key)
                
        update_kong_gw_plugin.delay(plugin_identifier ,filtered_data)
        
        return jsonify({
            "accept_data": filtered_data,
            "ignored_fields": list(ignored_fields),
            "message": "Plugin update request has been submitted."
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
        
        
@plugins_bp.route("/plugins/<plugin_identifier>", methods=["DELETE"])
def delete_plugin(plugin_identifier):
    try:
        plugin_to_delete = db.session.execute(
            db.select(PluginConfiguration).where(
                or_(
                    PluginConfiguration.id == plugin_identifier,
                    PluginConfiguration.instance_name == plugin_identifier
                )
            )
        )
        
        if plugin_to_delete is None:
            return jsonify({
                "error": "Plugin not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
        
        delete_kong_gw_plugin.delay(plugin_identifier)
        
        return jsonify({
            "message": "Plugin deletion request has been submitted."
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500