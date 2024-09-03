from app.plugin import plugin
from flask import request, jsonify, current_app as app
from app.models import API, Plugin, PluginAPIConfiguration
from app.async_tasks.async_plugin_tasks import async_create_plugin, async_update_plugin, async_delete_plugin
from app.extensions import db
from sqlalchemy import or_


@plugin.route("/plugins")
def list_plugins():
    try:
        plugins_list = Plugin.query.all()
        plugins_data = [plugin.to_dict() for plugin in plugins_list]

        return jsonify({
            "plugins": plugins_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugin.route("/plugins/<identifier>")
def get_plugin(identifier):
    try:
        plugin = db.session.execute(
            db.select(Plugin).where(Plugin.id == identifier)
        ).scalar()
        
        if plugin is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
            
        plugin_data = plugin.to_dict()
        
        return jsonify({
            "plugin": plugin_data
        })
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugin.route("/plugins/<identifier>/apis")
def list_apis_using_plugin(identifier):
    try:
        plugin = db.session.execute(
            db.select(Plugin).where(
                or_(
                    Plugin.id == identifier,
                    Plugin.name == identifier
                )
            )
        ).scalar()
        
        if plugin is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
            
        apis = db.session.execute(
            db.select(API)
            .join(PluginAPIConfiguration, PluginAPIConfiguration.api_id == API.id)
            .where(PluginAPIConfiguration.plugin_id == plugin.id)
        ).scalars().all()
        
        apis_data = [api.to_dict() for api in apis]

        return jsonify({
            "plugin": plugin.name,
            "APIs": apis_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugin.route("/apis/<api_identifier>/plugins")
def list_plugins_for_api(api_identifier):
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
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
        
        plugins_data = []
        for plugin_config in api.plugins:
            plugin_info = plugin_config.plugin.to_dict()
            plugin_info["config"] = plugin_config.config
            plugin_info["enabled"] = plugin_config.enabled
            plugin_info["kong_plugin_id"] = plugin_config.kong_plugin_id
            plugins_data.append(plugin_info)

        return jsonify({
            "api_id": api.id,
            "plugins": plugins_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugin.route("/apis/<api_identifier>/plugins/<plugin_identifier>")
def get_plugin_for_api(api_identifier, plugin_identifier):
    try:
        api = api = db.session.execute(
            db.select(API).where(
                or_(    
                    API.id == api_identifier,
                    API.name == api_identifier
                )
            )
        ).scalar()
        
        if api is None:
            return jsonify({
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
            
        plugin_data = None
        
        for plugin_config in api.plugins:
            if plugin_config.plugin_id == plugin_identifier:
                plugin_data = plugin_config.plugin.to_dict()
                plugin_data["config"] = plugin_config.config
                plugin_data["enabled"] = plugin_config.enabled
                plugin_data["kong_plugin_id"] = plugin_config.kong_plugin_id
                
                return jsonify({
                    "api_id": api.id,
                    "plugin": plugin_data
                }), 200
                
        return jsonify({
            "error": "Not found.",
            "message": "No plugin found with the provided identifier."
        }), 404     
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
        
@plugin.route("/apis/<api_identifier>/plugins", methods=["POST"])
def create_plugin_for_api(api_identifier):
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
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
            
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
        
        plugin_name = data.get("name")
        
        if plugin_name is None:
            return jsonify({
                "error": "Missing required field.",
                "message": "The required field 'name' must be provided."
            }), 400
            
        unknown_fields = {
            field: "unknown field" for field in data.keys()
            if field not in app.config["ALLOW_FIELDS_FOR_CREATE_PLUGIN"]
        }
                
        if unknown_fields:
            return jsonify({
                "error": "schema violation",
                "fields": unknown_fields
            }), 400
            
        existing_plugin = db.session.execute(
            db.select(PluginAPIConfiguration)
            .join(Plugin, Plugin.id == PluginAPIConfiguration.plugin_id)
            .where(
                PluginAPIConfiguration.api_id == api.id,
                Plugin.name == plugin_name
            )
        ).scalar()
        
        if existing_plugin:
            return jsonify({
                "error": "Conflict.",
                "message": f"The '{plugin_name}' plugin already exists for this API."
            }), 409
                
        async_create_plugin.delay(api_identifier, data)
        
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
        
        
@plugin.route("/apis/<api_identifier>/plugins/<plugin_identifier>", methods=["PATCH"])
def update_plugin_for_api(api_identifier, plugin_identifier):
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
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
            
        plugin = db.session.execute(
            db.select(PluginAPIConfiguration)
            .join(Plugin, Plugin.id == PluginAPIConfiguration.plugin_id)
            .where(
                PluginAPIConfiguration.api_id == api.id,
                or_(
                    Plugin.id == plugin_identifier,
                    Plugin.name == plugin_identifier
                )
            )
        ).scalar()
        
        if plugin is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
            
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
            
        unknown_fields = {
            field: "unknown field" for field in data.keys()
            if field not in app.config["ALLOW_PLUGIN_CONFIG_FIELDS"]
        }
                
        if unknown_fields:
            return jsonify({
                "error": "schema violation",
                "fields": unknown_fields
            }), 400
               
        async_update_plugin.delay(api_identifier, plugin_identifier, data)
        
        return jsonify({
            "message": "Plugin update request has been submitted."
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
        
        
@plugin.route("/apis/<api_identifier>/plugins/<plugin_identifier>", methods=["DELETE"])
def delete_plugin_for_api(api_identifier, plugin_identifier):
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
                "error": "Not found.",
                "message": "No API found with the provided identifier."
            }), 404
            
        plugin = db.session.execute(
            db.select(PluginAPIConfiguration)
            .join(Plugin, Plugin.id == PluginAPIConfiguration.plugin_id)
            .where(
                PluginAPIConfiguration.api_id == api.id,
                or_(
                    Plugin.id == plugin_identifier,
                    Plugin.name == plugin_identifier
                )
            )
        ).scalar()
        
        if plugin is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
               
        async_delete_plugin.delay(api_identifier, plugin_identifier)
        
        return jsonify({
            "message": "Plugin deletion request has been submitted."
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