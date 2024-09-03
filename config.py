class Config:
    SECRET_KEY = "kong-api-manager-secret-key"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:26032003@localhost:5432/kong_api_manager_db" 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOW_FIELDS_FOR_CREATE_API = {"name", "url", "path", "headers", "methods"}
    ALLOW_FIELDS_FOR_UPDATE_API = {"name", "url", "path", "headers", "methods", "enabled"}
    ALLOW_FIELDS_FOR_CREATE_PLUGIN = {"name", "config"}
    ALLOW_FIELDS_FOR_UPDATE_PLUGIN = {"config", "enabled"}
    CELERY_BROKER_URL = "amqp://localhost"
    KONG_ADMIN_URL = "http://localhost:8001"