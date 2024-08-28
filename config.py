class Config:
    SECRET_KEY = "kong-gw-api-manager-secret-key"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:26032003@localhost:5432/kong_api_manager_db" 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVICE_CONFIG_FIELDS = {
        "name", "host", "protocol", "port", "path",
        "retries", "connect_timeout", "write_timeout",
        "read_timeout", "tags", "client_certificate",
        "tls_verify", "tls_verify_depth", "ca_certificates", "url"
    }
    ROUTE_CONFIG_FIELDS = {
        "paths", "methods", "sources", "destinations", "name", 
        "headers", "hosts", "preserve_host","regex_priority", 
        "snis", "https_redirect_status_code", "service", 
        "response_buffering", "strip_path", "request_buffering"
    }
    PLUGIN_CONFIG_FIELDS = {
        "enable", "protocols", "ordering", "consumer",
        "consumer_group", "instance_name", "config",
        "name", "tags", "service", "route"
    }
    CELERY_BROKER_URL = "amqp://localhost"
    KONG_ADMIN_URL = "http://localhost:8001"