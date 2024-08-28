from sqlalchemy import String, Integer, Boolean, Text, ARRAY, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.inspection import inspect
from app.extensions import db
from typing import Optional


class ServiceConfiguration(db.Model):
    __tablename__ = "service_configuration"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  
    host: Mapped[str] = mapped_column(String(255), nullable=False)  
    name: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)  
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
    routes: Mapped[Optional[list["RouteConfiguration"]]] = relationship(back_populates="service")
    plugins: Mapped[Optional[list["PluginConfiguration"]]] = relationship(back_populates="service")
    
    
    def to_dict(self) -> dict:
        columns = [column.key for column in inspect(self).mapper.column_attrs]
        return {column: getattr(self, column) for column in columns}
       
    
    def refresh_updated_at(self, epoch_seconds):
        self.updated_at = epoch_seconds
        db.session.add(self)
        db.session.commit()


class RouteConfiguration(db.Model):
    __tablename__ = "route_configuration"

    id: Mapped[str] = mapped_column(String(50), primary_key=True) 
    paths: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)   
    methods: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    sources: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    destinations: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)   
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
    service_id: Mapped[Optional[str]] = mapped_column(ForeignKey("service_configuration.id"))
    service: Mapped[Optional["ServiceConfiguration"]] = relationship(back_populates="routes")
    plugins: Mapped[Optional[list["PluginConfiguration"]]] = relationship(back_populates="route")
    
    
    def to_dict(self) -> dict:
        columns = [column.key for column in inspect(self).mapper.column_attrs]
        return {column: getattr(self, column) for column in columns}
       
    
    def refresh_updated_at(self, epoch_seconds):
        self.updated_at = epoch_seconds
        db.session.add(self)
        db.session.commit()
        
        
class PluginConfiguration(db.Model):
    __tablename__ = "plugin_configuration"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    enable: Mapped[bool] = mapped_column(Boolean, default=True)
    protocols: Mapped[list[str]] = mapped_column(ARRAY(String), default=["grpc","grpcs","http","https"])
    ordering: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    consumer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    consumer_group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    instance_name: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    service_id: Mapped[Optional[str]] = mapped_column(ForeignKey("service_configuration.id"))
    service: Mapped[Optional["ServiceConfiguration"]] = relationship(back_populates="plugins")
    route_id: Mapped[Optional[str]] = mapped_column(ForeignKey("route_configuration.id"))
    route: Mapped[Optional["RouteConfiguration"]] = relationship(back_populates="plugins")
    
    
    def to_dict(self) -> dict:
        columns = [column.key for column in inspect(self).mapper.column_attrs]
        return {column: getattr(self, column) for column in columns}
       
    
    def refresh_updated_at(self, epoch_seconds):
        self.updated_at = epoch_seconds
        db.session.add(self)
        db.session.commit()