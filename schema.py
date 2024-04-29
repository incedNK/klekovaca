from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time


class Measurement(BaseModel):
    sensor_id: int
    temperature: float
    moisture: float
    date: date
    time: time

class SensorData(Measurement):
    id: int
    server_time_date: datetime
    
    class Config:
        from_attributes = True
    
class SensorBase(BaseModel):
    parcel_id: int
    config: Optional[int] = 30

class Sensor(SensorBase):
    id: int 
    date: datetime
    measurement: List[SensorData] = []
    
    class Config:
        from_attributes = True

class ParcelBase(BaseModel):
    name: str
    size: float

class Parcel(ParcelBase):
    id: int
    date: datetime
    owner_id: int
    devices: List[Sensor] = []
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    first_name: str 
    last_name: str
    email: EmailStr
    address: str
    is_admin: Optional[bool] = False
    
class UserCreate(UserBase):
    password: str

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


    