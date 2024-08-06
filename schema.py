from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time


class Measurement(BaseModel):
    sensor_id: int
    temperature: float
    moisture: float
    battery: float
    status: Optional[int]
    date: date
    time: time

class SensorData(Measurement):
    id: int
    server_time_date: datetime
    
    class Config:
        from_attributes = True
    
class SensorBase(BaseModel):
    parcel_id: int
    sensor_id: int
    config: Optional[int] = 30

class UpdateSensor(BaseModel):
    parcel_id: Optional[int] = None
    config: Optional[int] = None

class Sensor(SensorBase):
    id: int 
    date: datetime
    measurement: List[SensorData] = []
    
    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    parcel_id: int
    text: str
    is_active: Optional[bool] = True
    
class Alert(AlertBase):
    id: int
    date: datetime
    
    class Config:
        from_attributes = True

class ParcelBase(BaseModel):
    name: str
    crop_id: int

class UpdateParcel(BaseModel):
    name: Optional[str] = None
    crop_id: Optional[int] = None
    sow_complete: Optional[bool] = False

class Parcel(ParcelBase):
    id: int
    date: datetime
    owner_id: int
    devices: List[Sensor] = []
    alerts: List[Alert] = []
    
    class Config:
        from_attributes = True
        
class CropBase(BaseModel):
    name: str 
    temp_min: Optional[float]
    temp_max: Optional[float]
    temp_time_delta: Optional[float]
    moist_min: Optional[float]
    moist_max: Optional[float]
    moist_time_delta: Optional[float]

class ChangeCrop(BaseModel):
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    temp_time_delta: Optional[float] = None
    moist_min: Optional[float] = None
    moist_max: Optional[float] = None
    moist_time_delta: Optional[float] = None

class Crop(CropBase):
    id: int 
    date: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[int] = None
    is_admin: Optional[bool] = False
    email_alert: Optional[bool] = False
    sms_alert: Optional[bool] = False
    
class UserCreate(UserBase):
    password: str

class UserChange(BaseModel):
    password: Optional[str] = None
    phone: Optional[int] = None
    email_alert: Optional[bool] = None
    sms_alert: Optional[bool] = None

class AdminChange(BaseModel):
    is_admin: Optional[bool]

class User(UserBase):
    id: int
    date: datetime
    parcels: List[Parcel] = [] 
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    email: EmailStr | None = None


    