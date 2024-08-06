from dotenv import load_dotenv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.rest import Client
import requests

load_dotenv()

def sms_alert(phone_no: int, alert: str):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    
    client.messages.create(
        body = alert, 
        from_ = os.environ.get("TWILIO_PHONE"),
        to = f'+{phone_no}',
    )

def email_alert(email: str, alert1: str, alert2: str):
    port = 587
    smtp_server = "smtp-mail.outlook.com"
    sender = os.environ.get("EMAIL")
    receiver = email
    password = os.environ.get("MAILPASSWORD")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Request for secret key"
    msg["From"] = sender
    msg["To"] = receiver
    
    text = f'''Hello.\n
            This is automated alert send from our server.Please do not reply on this message.\n
            You received alert:\n
            {alert1}\n
            With regards.\n
            KlekovacaPZ Team\n\n
            ---------------------------------------------------------------------\n
            Pozdrav.\n
            Ovo je automatizovana poruka i nemojte odgovarati na nju.\n
            Dobili ste sljedece obavjestenje:\n
            {alert2}\n
            Srdacan pozdrav.\n
            KlekovacaPZ Tim\n
            '''
    body = MIMEText(text, 'plain')
    msg.attach(body)
    
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, receiver, msg.as_string())
    print("Email was sent!")
    server.quit()
    
def check_weather_conditions(lat: float, lon: float, crop_rain: float): 
    heavy_rain = 3 
    weather_data = []  
    forecast = []
    API_key = os.environ.get("OWM_API_KEY")
    response = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_key}&cnt=24')
    all_weather_data = response.json()['list']
    for data in all_weather_data:
        weather_data.append(data['pop'])
    for i in range(0, len(weather_data), 8):
        forecast.append(weather_data[i:i+8])
    m = []
    for x in forecast:
        m.append([i for i in x if i  > 0.8])
        
        pop = [{((j+1)*24) : ((sum(forecast[j])/len(forecast[j]))) for j in range(len(forecast))}, {((y+1)*24) : (sum(m[y])/8) for y in range(len(m))}]
    real_pop = {k : [d[k] for d in pop] for k in pop[0]}
    
    res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_key}&cnt=8')
    todays_rain_dict = res.json()['list']
    today_rain_list = [dict['rain']['3h'] for dict in todays_rain_dict if 'rain' in dict]
    rain = sum(today_rain_list)/8
    if rain < heavy_rain:
        rain_forecast = {'rain_prob': real_pop[(crop_rain*24)][0], 'heavy_rain': real_pop[(crop_rain*24)][1]}
        return rain_forecast
    