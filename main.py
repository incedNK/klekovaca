from fastapi import FastAPI, Form, Depends, HTTPException, status
import uvicorn
from typing import Annotated, List
from dateutil.parser import parse
from datetime import datetime, date, timedelta
import os
from jose import jwt, JWTError
from fastapi_sqlalchemy import DBSessionMiddleware, db
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import models
import schema
import config
import utils
import shapely
from dotenv import load_dotenv

load_dotenv() 

password = os.environ.get("PASSWORD")
klekovaca = os.environ.get("POSTGRES_DB")
host = os.environ.get("HOST")
port= os.environ.get("PORT")

DATABASE_URL = f'postgresql+psycopg2://postgres:{password}@{host}:{port}/{klekovaca}'

app = FastAPI()
app.add_middleware(DBSessionMiddleware, db_url=DATABASE_URL)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def get_current_user(token: Annotated[str, Depends(config.oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=[os.environ.get("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schema.TokenData(email=username)
    except JWTError:
        raise credentials_exception
    user = db.session.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def create_alert(parcel_id: int, text2: str, text1: str):
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == parcel_id).first()
    user = db.session.query(models.User).filter(models.User.id == parcel.owner_id).first()
    if user.sms_alert:
        utils.sms_alert(phone_no=user.phone, alert=text2)
    if user.email_alert:
        utils.email_alert(email=user.email, alert1=text1, alert2=text2)
    db_alert = models.Alert(parcel_id=parcel_id, text=text2, is_active=True)
    try:
        db.session.add(db_alert)
        db.session.commit()
        return {'detail': 'Alert created'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

def check_crop_conditions(sensor_id: int, temp: float, moisture: float):
    sensor = db.session.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == sensor.parcel_id).first()
    crop = db.session.query(models.Crop).filter(models.Crop.id == parcel.crop_id).first()
    coords = []
    loc = sensor.location
    if loc:
        sensor_location = shapely.wkb.loads(bytes(loc.data), hex=True)
        coords.append(sensor_location)
    if crop.season_start.date() < date.today() < crop.season_end.date():
        if not parcel.sow_complete:
            if crop.temp_min < temp < crop.temp_max:
                if crop.moist_min < moisture < crop.moist_max:
                    forecast = utils.check_weather_conditions(lat=coords[0].x, lon=coords[0].y, crop_rain=crop.rain)
                    r_p = forecast['rain_prob']
                    h_r = forecast["heavy_rain"]
                    if r_p < 0.3:
                        text1 = 'Optimal conditions. Low chance for rain in following days.'
                        text2 = 'Optimalni uslovi za sjetvu. Mala sansa za kisu u narednim danima.'
                    elif r_p < 0.5 and h_r < 0.3:
                        text1 = f'Optimal conditions but low chance for rain (less than 50%) with heavy rain chance {(h_r * 100)}%.'
                        text2 = f'Optimalni uslovi za sjetvu sa malom sansom za kisu (<50%) i sa sansom za pljuskove {(h_r * 100)}%'
                    create_alert(parcel_id=parcel.id, text2=text2, text1=text1)
    

# Users routes
@app.get('/me', tags=['Users'], response_model=schema.User)
def get_user(current_user: str = Depends(get_current_user)):
    user = db.session.query(models.User).filter(models.User.id == current_user.id).first()
    return user
        
@app.get('/users', response_model=List[schema.User], tags=['Users'])
def get_users(current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    users = db.session.query(models.User).all()
    return users    

@app.post("/token", tags=['Users'])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> schema.Token:
    exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.session.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise exception
    if not config.verify_password(form_data.password, user.hashed_password):
        raise exception
    access_token = config.create_access_token(data={"sub": user.email})
    return schema.Token(access_token=access_token, token_type="bearer")

@app.post('/user', tags=['Users'])
def create_user(user: schema.UserCreate, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_user = models.User(email=user.email, hashed_password=config.get_password_hash(user.password), 
                          is_admin=user.is_admin, email_alert=user.email_alert, sms_alert=user.sms_alert, phone=user.phone)
    if db_user.email == "admin@mail.com":
        db_user.is_admin = True
    user_exists = db.session.query(models.User).filter(models.User.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Username already exists")
    try:
        db.session.add(db_user)
        db.session.commit()
        return {"detail": "Successfully created new user!"}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.patch('/user/{id}', tags=['Users'], response_model_exclude_none=True)
def change_user(id: int, user_data: schema.UserChange, current_user: str = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        entry = {}
        db_user = db.session.query(models.User).filter(models.User.id == id)
        if not db_user.first():
            return {'detail': 'No such user.'}
        if user_data.password:
            entry['hashed_password'] = config.get_password_hash(password=user_data.password)
        if user_data.email_alert:
            entry['email_alert'] = user_data.email_alert
        if user_data.sms_alert:
            entry['sms_alert'] = user_data.sms_alert
        if user_data.phone:
            entry['phone'] = user_data.phone
        entry['date'] = datetime.now()
        db_user.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': 'Successfully changed data'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}
    
@app.patch('/admin/{id}', tags=['Users'])
def change_priviliges(id: int, data: schema.AdminChange, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        db_user = db.session.query(models.User).filter(models.User.id == id)
        if not db_user.first():
            return {'detail': 'No such user.'}
        entry = data.dict()
        entry['date'] = datetime.now()
        db_user.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': 'Successfully changed data'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.delete('/user/{id}', tags=['Users'])
def delete_user(id: int, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to remove user"
        )
    try:
        db_user = db.session.query(models.User).filter(models.User.id == id)
        if not db_user.first():
            return {'detail': 'No such user.'}
        db_user.delete(synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfuly deleted user {id}'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}    

# Parcel routes
@app.post('/parcel', tags=['Parcels'])
def create_parcel(parcel: schema.ParcelBase, current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_parcel = models.Parcel(name=parcel.name, owner_id=current_user.id, crop_id=parcel.crop_id, sow_complete=False)
    try:
        db.session.add(db_parcel)
        db.session.commit()
        return {"detail": "Successfully added new parcel!"}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.patch('/parcel/{id}', tags=['Parcels'], response_model_exclude_none=True)
def change_parcel(id: int, parcel: schema.UpdateParcel, current_user: str = Depends(get_current_user)):
    db_parcel = db.session.query(models.Parcel).filter(models.Parcel.id == id)
    if not db_parcel.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find parcel in database"
        )
    users_parcel = db_parcel.first()
    if current_user.id != users_parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        entry = {}
        if parcel.name:
            entry['name'] = parcel.name
        if parcel.crop_id:
            entry['crop_id'] = parcel.crop_id
        entry['date'] = datetime.now()
        db_parcel.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': 'Successfully altered parcel data'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.delete('/parcel/{id}', tags=['Parcels'])
def delete_parcel(id: int, current_user: str = Depends(get_current_user)):
    db_parcel = db.session.query(models.Parcel).filter(models.Parcel.id == id)
    if not db_parcel.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find parcel in database"
        )
    users_parcel = db_parcel.first()
    if current_user.id != users_parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        db_parcel.delete(synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfully deleted parcel {id}'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

# Sensor routes
@app.get('/sensors', tags=['Sensors'])
def get_sensors(current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    sensors = db.session.query(models.Sensor).all()
    return sensors

@app.post('/sensor', tags=['Sensors'])
def create_sensor(sensor: schema.SensorBase, current_user: str = Depends(get_current_user)):
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == sensor.parcel_id).first()
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such parcel")
    if current_user.id != parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_sensor = models.Sensor(parcel_id=parcel.id, sensor_id=sensor.sensor_id, config=sensor.config)
    try:
        db.session.add(db_sensor)
        db.session.commit()
        return {"detail": "Successfully added new sensor!"}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.patch('/sensor/{id}', tags=['Sensors'], response_model_exclude_none=True)
def change_sensor(id: int, sensor: schema.UpdateSensor, current_user: str = Depends(get_current_user)):
    db_sensor = db.session.query(models.Sensor).filter(models.Sensor.id == id)
    existing_sensor = db_sensor.first()
    if not existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sensor found")
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == existing_sensor.parcel_id).first()
    if current_user.id != parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        entry = {}
        if sensor.config:
            entry['config'] = sensor.config
        if sensor.parcel_id:
            entry['parcel_id'] = sensor.parcel_id
        entry['date'] = datetime.now()
        db_sensor.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': 'Successfully update sensor'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.delete('/sensor/{id}', tags=['Sensors'])
def delete_sensor(id: int, current_user: str = Depends(get_current_user)):
    db_sensor = db.session.query(models.Sensor).filter(models.Sensor.id == id)
    existing_sensor = db_sensor.first()
    if not existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sensor found")
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == existing_sensor.parcel_id).first()
    if current_user.id != parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        db_sensor.delete(synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfully deleted sensor {id}'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

# Crops routes
@app.get('/crop', tags=['Crops'], response_model=List[schema.Crop])
def get_crops():
    crops = db.session.query(models.Crop).all()
    return crops

@app.post('/crop', tags=['Crops'])
def create_crop(crop: schema.CropBase, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_crop = models.Crop(name=crop.name, temp_min=crop.temp_min, temp_max=crop.temp_max, moist_min=crop.moist_min, 
                          moist_max=crop.moist_max)
    try:
        db.session.add(db_crop)
        db.session.commit()
        return {'detail': 'Successfully added new crop!'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}
    
@app.patch('/crop/{id}', tags=['Crops'], response_model_exclude_none=True)
def change_crop(id: int, crop: schema.ChangeCrop, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_crop = db.session.query(models.Crop).filter(models.Crop.id == id)
    if not db_crop.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such crop found")
    entry = {}
    if crop.temp_min:
        entry['temp_min'] = crop.temp_min
    if crop.temp_max:
        entry['temp_max'] = crop.temp_max
    if crop.temp_time_delta:
        entry['temp_time_delta'] = crop.temp_time_delta
    if crop.moist_min:
        entry['moist_min'] = crop.moist_min
    if crop.moist_max:
        entry['moist_max'] = crop.moist_max
    if crop.moist_time_delta:
        entry['moist_time_delta'] = crop.moist_time_delta
    entry['date'] = datetime.now()
    try:
        db_crop.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': 'Successfully changed crop!'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.delete('/crop/{id}', tags=['Crops'])
def delete_crop(id: int, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_crop = db.session.query(models.Crop).filter(models.Crop.id == id)
    if not db_crop.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such crop found")
    try:
        db_crop.delete(synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfully deleted crop {id}'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

# Alerts
@app.patch('/alert/{id}', tags=['Alerts'])
def inactivate_alert(id: int, current_user: str = Depends(get_current_user)):
    alert = db.session.query(models.Alert).filter(models.Alert.id == id)
    active_alert = alert.first()
    if not active_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert found")
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == active_alert.parcel_id).first()
    if current_user.id != parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        entry = {'is_active': False, 'date': datetime.now()}
        alert.update(entry, synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfully changed alert'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.delete('/alert/{id}', tags=['Alerts'])
def inactivate_alert(id: int, current_user: str = Depends(get_current_user)):
    alert = db.session.query(models.Alert).filter(models.Alert.id == id)
    active_alert = alert.first()
    if not active_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert found")
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == active_alert.parcel_id).first()
    if current_user.id != parcel.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    try:
        alert.delete(synchronize_session=False)
        db.session.commit()
        return {'detail': f'Successfully deleted alert {id}'}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}     

# Sensor data and alert routes
@app.get('/data/{id}', response_model=List[schema.Measurement], tags=['Data'])
def get_sensor_data(id: int):
    sensor_data = db.session.query(models.SensorData).filter(models.SensorData.sensor_id == id).all()
    return sensor_data

@app.post('/data', tags=['Data'])
def create_data(sensor_id: Annotated [int, Form()], temperature: Annotated[int, Form()], moisture: Annotated[int, Form()], battery: Annotated[int, Form()],
                status: Annotated[int, Form()], date: Annotated[str, Form()], time: Annotated[str, Form()]):
    datetime_date = datetime.strptime(date, "%Y-%m-%d")
    datetime_time = datetime.strptime(time, "%H:%M")
    data = {'sensor_id': sensor_id, 'temperature': temperature/10, 'moisture': moisture/10, 'battery': battery/100, 'date': datetime_date.date(), 
            'time': datetime_time.time(), 'status': status}
    sensor = db.session.query(models.Sensor).filter(models.Sensor.sensor_id == sensor_id).first()
    db_measurement = models.SensorData(sensor_id=data["sensor_id"], temperature=data["temperature"], moisture=data["moisture"], battery=data["battery"],
                                       status=data["status"], date=data["date"], time=data["time"])
    
    try:
        if not sensor:
            return
        else:
            db.session.add(db_measurement)
            db.session.commit()
            check_crop_conditions(sensor_id=sensor.id, temp=temperature/10, moisture=moisture/10)
            return f'$1&${sensor.config}&#'
    except Exception as e:
        print(e)
        return '$0&$0&#'

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)