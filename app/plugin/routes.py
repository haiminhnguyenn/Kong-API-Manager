from app.plugin import plugin
from flask import request, jsonify, current_app as app
from app.models import API, Plugin, PluginAPIConfiguration
from app.extensions import db
from sqlalchemy import or_
from app.kong_client.plugin_client import create_plugin_in_kong, update_plugin_in_kong, delete_plugin_in_kong


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
        
        
@plugin.route("/plugins/<plugin_identifier>")
def get_plugin(plugin_identifier):
    try:
        plugin = db.session.execute(
            db.select(Plugin).where(Plugin.id == plugin_identifier)
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
    
    finally:
        db.session.close()
        
        
@plugin.route("/plugins/<plugin_identifier>/apis")
def list_apis_using_plugin(plugin_identifier):
    try:
        plugin = db.session.execute(
            db.select(Plugin).where(
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
        
    finally:
        db.session.close()
        
        
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
            plugin_info.update({
                "config": plugin_config.config,
                "enabled": plugin_config.enabled,
                "kong_plugin_id": plugin_config.kong_plugin_id,
                "created_at": plugin_config.created_at,
                "updated_at": plugin_config.updated_at
            })
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
        
    finally:
        db.session.close()
        
        
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
            
        plugin_config = db.session.execute(
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
        
        if plugin_config is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
        
        plugin_data = plugin_config.plugin.to_dict()
        plugin_data.update({
            "config": plugin_config.config,
            "enabled": plugin_config.enabled,
            "kong_plugin_id": plugin_config.kong_plugin_id,
            "created_at": plugin_config.created_at,
            "updated_at": plugin_config.updated_at
        })
        
        return jsonify({
            "api_id": api.id,
            "plugin": plugin_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error.",
            "message": str(e)
        }), 500
        
    finally:
        db.session.close()
        
        
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
                
        config, kong_plugin_id, error = create_plugin_in_kong(api.kong_service_id, data)
        
        if error:
            return jsonify({
                "error": "Plugin creation failed.",
                "message": error
            }), 500
            
        plugin = db.session.execute(
            db.select(Plugin).where(Plugin.name == plugin_name)
        ).scalar()
            
        if plugin is None:
            plugin = Plugin(name=plugin_name)
            db.session.add(plugin)

        plugin_config = PluginAPIConfiguration(
            config=config,
            kong_plugin_id=kong_plugin_id,
            plugin=plugin,
            api=api
        )
        
        db.session.add(plugin_config)
        db.session.commit()
        return jsonify({
            "message": "Plugin created successfully.",
            "plugin_id": plugin.id
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
            
        plugin_config_to_update = db.session.execute(
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
        
        if plugin_config_to_update is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
            
        data = request.get_json()
        
        if data is None:
            raise ValueError("Invalid JSON data.")
            
        unknown_fields = {
            field: "unknown field" for field in data.keys()
            if field not in app.config["ALLOW_FIELDS_FOR_UPDATE_PLUGIN"]
        }
                
        if unknown_fields:
            return jsonify({
                "error": "schema violation",
                "fields": unknown_fields
            }), 400
               
        status, error = update_plugin_in_kong(plugin_config_to_update.kong_plugin_id, data)
        
        if status == "failure":
            return jsonify({
                "error": "Plugin update failed.",
                "message": error
            }), 500
            
        for key, value in data.items():
            setattr(plugin_config_to_update, key, value)
            
        db.session.commit()
        return jsonify({
            "message": "Plugin updated successfully."
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
            
        plugin_config_to_delete = db.session.execute(
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
        
        if plugin_config_to_delete is None:
            return jsonify({
                "error": "Not found.",
                "message": "No plugin found with the provided identifier."
            }), 404
               
        status, error = delete_plugin_in_kong(plugin_config_to_delete.kong_plugin_id)
        
        if status == "failure":
            return jsonify({
                "error": "Plugin deletion failed.",
                "message": error
            }), 500
        
        db.session.delete(plugin_config_to_delete)
        db.session.commit()
        return jsonify({
            "message": "Plugin deleted successfully."
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