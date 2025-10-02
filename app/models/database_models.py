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
    MANUAL = "manual"  # For tourist-reported incidents via E-FIR


class AlertSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ZoneType(enum.Enum):
    SAFE = "safe"
    RISKY = "risky"
    RESTRICTED = "restricted"


class BroadcastType(enum.Enum):
    RADIUS = "radius"
    ZONE = "zone"
    REGION = "region"
    ALL = "all"


class BroadcastSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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
    phone = Column(String, nullable=True)  # For emergency contact
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


class EFIR(Base):
    """Electronic First Information Report - Immutable blockchain-backed records"""
    __tablename__ = "efirs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    efir_number = Column(String, unique=True, nullable=False)  # EFIR-YYYYMMDD-NNNN
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)  # Nullable for tourist reports
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    tourist_id = Column(String, ForeignKey("tourists.id"), nullable=False)
    
    # Blockchain data
    blockchain_tx_id = Column(String, unique=True, nullable=False)
    block_hash = Column(String, nullable=True)
    chain_id = Column(String, nullable=True)
    
    # E-FIR content (immutable)
    incident_type = Column(String, nullable=False)  # sos, harassment, theft, etc.
    severity = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_description = Column(String, nullable=True)
    
    # Tourist information (snapshot at time of E-FIR)
    tourist_name = Column(String, nullable=False)
    tourist_email = Column(String, nullable=False)
    tourist_phone = Column(String, nullable=True)
    
    # Authority information (nullable for tourist self-reports)
    reported_by = Column(String, ForeignKey("authorities.id"), nullable=True)
    officer_name = Column(String, nullable=True)
    officer_badge = Column(String, nullable=True)
    officer_department = Column(String, nullable=True)
    
    # Report source: 'tourist' or 'authority'
    report_source = Column(String, nullable=True)  # 'tourist', 'authority'
    
    # Additional details
    witnesses = Column(Text, nullable=True)  # JSON array
    evidence = Column(Text, nullable=True)  # JSON array of evidence items
    officer_notes = Column(Text, nullable=True)
    
    # Status (only for tracking, not for modification)
    is_verified = Column(Boolean, default=True)
    verification_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps (immutable)
    incident_timestamp = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Additional metadata
    additional_data = Column(Text, nullable=True)  # JSON for additional data


class UserDevice(Base):
    """Stores device tokens for push notifications"""
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("tourists.id", ondelete="CASCADE"), nullable=False)
    device_token = Column(String, unique=True, nullable=False)  # FCM token
    device_type = Column(String, nullable=False)  # 'ios' or 'android'
    device_name = Column(String, nullable=True)  # e.g., "iPhone 13 Pro"
    app_version = Column(String, nullable=True)  # e.g., "1.0.0"
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    tourist = relationship("Tourist", backref="devices")


class EmergencyBroadcast(Base):
    """Emergency broadcasts sent to tourists in specific areas"""
    __tablename__ = "emergency_broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(String, unique=True, nullable=False)  # BCAST-YYYYMMDD-NNNN
    broadcast_type = Column(Enum(BroadcastType, name='broadcast_type', values_callable=lambda obj: [e.name for e in obj]), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(BroadcastSeverity, name='broadcast_severity', values_callable=lambda obj: [e.name for e in obj]), nullable=False)
    alert_type = Column(String, nullable=True)  # natural_disaster, security_threat, etc.
    action_required = Column(String, nullable=True)  # evacuate, avoid_area, stay_indoors

    # Radius broadcast fields
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    radius_km = Column(Float, nullable=True)

    # Zone broadcast fields
    zone_id = Column(Integer, ForeignKey("restricted_zones.id", ondelete="SET NULL"), nullable=True)

    # Region broadcast fields (JSON: {min_lat, max_lat, min_lon, max_lon})
    region_bounds = Column(Text, nullable=True)

    # Metadata
    tourists_notified_count = Column(Integer, default=0)
    devices_notified_count = Column(Integer, default=0)
    acknowledgment_count = Column(Integer, default=0)

    # Authority info
    sent_by = Column(String, ForeignKey("authorities.id"), nullable=False)
    department = Column(String, nullable=True)

    # Timestamps
    expires_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    zone = relationship("RestrictedZone", backref="broadcasts")
    authority = relationship("Authority", backref="broadcasts")
    acknowledgments = relationship("BroadcastAcknowledgment", back_populates="broadcast")


class BroadcastAcknowledgment(Base):
    """Tourist acknowledgments of broadcast messages"""
    __tablename__ = "broadcast_acknowledgments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("emergency_broadcasts.id", ondelete="CASCADE"), nullable=False)
    tourist_id = Column(String, ForeignKey("tourists.id", ondelete="CASCADE"), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=True)  # 'safe', 'need_help', 'evacuating'
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    broadcast = relationship("EmergencyBroadcast", back_populates="acknowledgments")
    tourist = relationship("Tourist", backref="broadcast_acknowledgments")
