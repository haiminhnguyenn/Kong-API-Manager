from app.extensions import db
from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional


class ServiceConfiguration(db.Model):
    __tablename__ = "service_configuration"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  
    host: Mapped[str] = mapped_column(String(255), nullable=False)  
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  
    enable: Mapped[bool] = mapped_column(Boolean, default=True)
    connect_timeout: Mapped[int] = mapped_column(Integer, default=60000)
    read_timeout: Mapped[int] = mapped_column(Integer, default=60000)
    retries: Mapped[int] = mapped_column(Integer, default=5)
    protocol: Mapped[str] = mapped_column(String(6), default="http")  
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  
    port: Mapped[int] = mapped_column(Integer, default=80)  
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  
    client_certificate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  
    tls_verify: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)  
    tls_verify_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    write_timeout: Mapped[int] = mapped_column(Integer, default=60000)
    ca_certificates: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    
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