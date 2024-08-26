class Config:
    SECRET_KEY = "kong-gw-api-manager-secret-key"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgre:26032003@localhost:5432/kong_gateway_manager_db" 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVICE_CONFIG_FIELDS = {
        "name", "host", "protocol", "port", "path",
        "retries", "connect_timeout", "write_timeout",
        "read_timeout", "tags", "client_certificate",
        "tls_verify", "tls_verify_depth", "ca_certificates", "url"
    }
    CELERY_BROKER_URL = "amqp://localhost"
    KONG_ADMIN_URL = "http://localhost:8001"