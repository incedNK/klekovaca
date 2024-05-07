from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, ForeignKey, DateTime
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String)
    address = Column(String)
    is_admin = Column(Boolean)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    parcels = relationship("Parcel", back_populates="owners")

class Parcel(Base):
    __tablename__ = "parcels"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    name = Column(String)
    size = Column(Float)
    location = Column(Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True))
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    owners = relationship("User", back_populates="parcels")
    devices = relationship("Sensor", back_populates="sensor_locations")

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True)
    parcel_id = Column(Integer, ForeignKey('parcels.id', ondelete="CASCADE"), nullable=False)
    sensor_id = Column(Integer, unique=True, nullable=False)
    config = Column(Integer)
    location = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    sensor_locations = relationship("Parcel", back_populates="devices")
    measurement = relationship("SensorData", back_populates="data")

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, nullable=False)
    temperature = Column(Float)
    moisture = Column(Float)
    date = Column(Date)
    time = Column(Time)
    server_time_date = Column(DateTime(timezone=True), server_default=func.now())
    
    data = relationship("Sensor", back_populates="measurement")
    