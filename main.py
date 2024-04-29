from fastapi import FastAPI, Form, Depends, HTTPException, status
import uvicorn
from typing import Annotated, List
from datetime import datetime
import os
from jose import jwt, JWTError
from fastapi_sqlalchemy import DBSessionMiddleware, db
from fastapi.security import OAuth2PasswordRequestForm
import models
import schema
import config
from dotenv import load_dotenv

load_dotenv() 

password = os.environ.get("PASSWORD")
klekovaca = os.environ.get("POSTGRES_DB")
host = os.environ.get("HOST")
port= os.environ.get("PORT")

DATABASE_URL = f'postgresql+psycopg2://postgres:{password}@{host}:{port}/{klekovaca}'

app = FastAPI()
app.add_middleware(DBSessionMiddleware, db_url=DATABASE_URL)

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
    

@app.get('/')
async def home():
    return {'message': 'Welcome Page.'}

@app.get('/users', response_model=List[schema.User])
def get_users(current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    users = db.session.query(models.User).all()
    return users

@app.get('/sensors')
def get_users(current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    sensors = db.session.query(models.Sensor).all()
    return sensors
    

@app.post("/token")
def get_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> schema.Token:
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

@app.post('/user')
def create_user(user: schema.UserCreate, current_user: str = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_user = models.User(first_name=user.first_name, last_name=user.last_name, email=user.email, 
                          hashed_password=config.get_password_hash(user.password), address=user.address)
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

@app.post('/parcel')
def create_parcel(parcel: schema.ParcelBase, current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    db_parcel = models.Parcel(name=parcel.name, size=parcel.size, owner_id=current_user.id)
    try:
        db.session.add(db_parcel)
        db.session.commit()
        return {"detail": "Successfully added new parcel!"}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.post('/sensor')
def create_parcel(sensor: schema.SensorBase, current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update database"
        )
    parcel = db.session.query(models.Parcel).filter(models.Parcel.id == sensor.parcel_id).first()
    db_sensor = models.Sensor(parcel_id=parcel.id)
    try:
        db.session.add(db_sensor)
        db.session.commit()
        return {"detail": "Successfully added new sensor!"}
    except Exception as e:
        print(e)
        return {"detail": "There was problem with database entry. Try later."}

@app.post('/data')
def create_data(sensor_id: Annotated [int, Form()], temperature: Annotated[int, Form()], moisture: Annotated[int, Form()], 
                date: Annotated[str, Form()], time: Annotated[str, Form()]):
    datetime_date = datetime.strptime(date, "%Y-%m-%d")
    datetime_time = datetime.strptime(time, "%H:%M")
    data = {'sensor_id': sensor_id, 'temperature': temperature/10, 'moisture': moisture/10, 'date': datetime_date.date(), 
            'time': datetime_time.time()}
    conf = db.session.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    db_measurement = models.SensorData(sensor_id=data["sensor_id"], temperature=data["temperature"], moisture=data["moisture"], 
                                       date=data["date"], time=data["time"])
    try:
        db.session.add(db_measurement)
        db.session.commit()
        return f'$1&${conf.config}&#'
    except Exception as e:
        print(e)
        return '$0&$0&#'

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)