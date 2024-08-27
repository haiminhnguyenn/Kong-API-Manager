from app.extensions import db
from sqlalchemy import String, Integer, Boolean, ARRAY, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional


class RouteConfiguration(db.Model):
    __tablename__ = "route_configuration"

    id: Mapped[str] = mapped_column(String(50), primary_key=True) 
    paths: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)   
    methods: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    sources: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    destinations: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)   
    headers: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    hosts: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    preserve_host: Mapped[bool] = mapped_column(Boolean, default=False) 
    regex_priority: Mapped[int] = mapped_column(Integer, default=0) 
    snis: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    https_redirect_status_code: Mapped[int] = mapped_column(Integer, default=426) 
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    protocols: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), default=["http","https"])
    path_handling: Mapped[str] = mapped_column(String, default="v0") 
    response_buffering: Mapped[bool] = mapped_column(Boolean, default=True) 
    strip_path: Mapped[bool] = mapped_column(Boolean, default=True) 
    request_buffering: Mapped[bool] = mapped_column(Boolean, default=True) 
    created_at: Mapped[int] = mapped_column(Integer, nullable=False) 
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)
    service_id: Mapped[str] = mapped_column(ForeignKey("service_configuration.id"), nullable=False)
    service: Mapped["ServiceConfiguration"] = relationship(
        "ServiceConfiguration",
        back_populates="routes"
    )
    
    
    def to_dict(self):
        return {
            "id": self.id,
            "host": self.host,
            "name": self.name,
            "enable": self.enable,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "retries": self.retries,
            "protocol": self.protocol,
            "path": self.path,
            "port": self.port,
            "tags": self.tags,
            "client_certificate": self.client_certificate,
            "tls_verify": self.tls_verify,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tls_verify_depth": self.tls_verify_depth,
            "write_timeout": self.write_timeout,
            "ca_certificates": self.ca_certificates
        }
       
    
    def refresh_updated_at(self, epoch_seconds):
        self.updated_at = epoch_seconds
        db.session.add(self)
        db.session.commit()