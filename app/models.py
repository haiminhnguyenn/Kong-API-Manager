from sqlalchemy import String, Integer, Boolean, ARRAY, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.inspection import inspect
from app.extensions import db
from typing import Optional
from datetime import datetime, timezone
import uuid


class TimestampMixin:
    created_at: Mapped[int] = mapped_column(
        Integer, 
        default=lambda: int(datetime.now(timezone.utc).timestamp()),  
        nullable=False
    )
    updated_at: Mapped[int] = mapped_column(
        Integer, 
        default=lambda: int(datetime.now(timezone.utc).timestamp()), 
        onupdate=lambda: int(datetime.now(timezone.utc).timestamp()), 
        nullable=False
    )


class PluginAPIConfiguration(TimestampMixin, db.Model):
    __tablename__ = "plugin_api_configuration"
    
    plugin_id: Mapped[str] = mapped_column(ForeignKey("plugin.id"), primary_key=True)
    api_id: Mapped[str] = mapped_column(ForeignKey("api.id"), primary_key=True)     
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    kong_plugin_id: Mapped[Optional[str]] = mapped_column(String(36))
    plugin: Mapped["Plugin"] = relationship(back_populates="apis")
    api: Mapped["API"] = relationship(back_populates="plugins")


class API(TimestampMixin, db.Model):
    __tablename__ = "api"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  
    name: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)  
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    path: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    methods: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(10)), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    kong_service_id: Mapped[Optional[str]] = mapped_column(String(36))
    kong_route_id: Mapped[Optional[str]] = mapped_column(String(36))
    plugins: Mapped[Optional[list["PluginAPIConfiguration"]]] = relationship(
        back_populates="api",
        cascade="all, delete-orphan"
    )

    
    def to_dict(self) -> dict:
        columns = [column.key for column in inspect(self).mapper.column_attrs]
        return {column: getattr(self, column) for column in columns}


class Plugin(db.Model):
    __tablename__ = "plugin"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    apis: Mapped[list["PluginAPIConfiguration"]] = relationship(back_populates="plugin")
    
    
    def to_dict(self) -> dict:
        columns = [column.key for column in inspect(self).mapper.column_attrs]
        return {column: getattr(self, column) for column in columns}