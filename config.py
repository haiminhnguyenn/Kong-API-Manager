class Config:
    SECRET_KEY = "kong-gw-api-manager-secret-key"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:26032003@localhost:5432/kong_gateway_manager_db" 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVICE_CONFIG_FIELDS = {
        "name", "host", "protocol", "port", "path",
        "retries", "connect_timeout", "write_timeout",
        "read_timeout", "tags", "client_certificate",
        "tls_verify", "tls_verify_depth", "ca_certificates", "url"
    }
    ROUTE_CONFIG_FIELDS = {
        "paths", "methods", "sources","destinations",
        "name", "headers", "hosts", "preserve_host",
        "regex_priority", "snis", "https_redirect_status_code",
        "tags", "protocols", "path_handling", "id",
        "updated_at", "service", "response_buffering",
        "strip_path", "request_buffering", "created_at"
    }
    CELERY_BROKER_URL = "amqp://localhost"
    KONG_ADMIN_URL = "http://localhost:8001"