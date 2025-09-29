from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()


class UserRole(enum.Enum):
    TOURIST = "tourist"
    AUTHORITY = "authority"
    ADMIN = "admin"


class TripStatus(enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AlertType(enum.Enum):
    GEOFENCE = "geofence"
    ANOMALY = "anomaly"
    PANIC = "panic"
    SOS = "sos"
    SEQUENCE = "sequence"


class AlertSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ZoneType(enum.Enum):
    SAFE = "safe"
    RISKY = "risky"
    RESTRICTED = "restricted"


class Tourist(Base):
    __tablename__ = "tourists"

    id = Column(String, primary_key=True)  # Supabase UUID
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    emergency_contact = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # For local auth
    safety_score = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_location_lat = Column(Float, nullable=True)
    last_location_lon = Column(Float, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trips = relationship("Trip", back_populates="tourist")
    locations = relationship("Location", back_populates="tourist")
    alerts = relationship("Alert", back_populates="tourist")


class Authority(Base):
    __tablename__ = "authorities"

    id = Column(String, primary_key=True)  # Supabase UUID
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    badge_number = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    rank = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # For local auth
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tourist_id = Column(String, ForeignKey("tourists.id"), nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.PLANNED)
    itinerary = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tourist = relationship("Tourist", back_populates="trips")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tourist_id = Column(String, ForeignKey("tourists.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tourist = relationship("Tourist", back_populates="locations")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tourist_id = Column(String, ForeignKey("tourists.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    alert_metadata = Column(Text, nullable=True)  # JSON string for additional data
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String, ForeignKey("authorities.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tourist = relationship("Tourist", back_populates="alerts")


class RestrictedZone(Base):
    __tablename__ = "restricted_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    zone_type = Column(Enum(ZoneType), nullable=False)
    # Simple lat/lon bounds for zone definition (center point and radius or bounding box)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=True)  # For circular zones
    bounds_json = Column(Text, nullable=True)  # JSON string for complex polygon bounds
    is_active = Column(Boolean, default=True)
    created_by = Column(String, ForeignKey("authorities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    incident_number = Column(String, unique=True, nullable=False)
    status = Column(String, default="open")
    priority = Column(String, nullable=True)
    assigned_to = Column(String, ForeignKey("authorities.id"), nullable=True)
    response_time = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    efir_reference = Column(String, nullable=True)  # Blockchain reference
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())