import os

import requests
from flask import Flask

import alerts
from positions import app as positions_app
from alerts import app as alerts_app
from flask_cors import CORS
from flask_apscheduler import APScheduler
import datetime
import json

class Config:
    SCHEDULER_API_ENABLED = True
app = Flask(__name__)

app.config.from_object(Config)
CORS(app)


scheduler = APScheduler()

# Scheduled job example
@scheduler.task('interval', id='call_api_job', seconds=60, misfire_grace_time=900)
def call_api_job():
    print(f"Scheduler running at {datetime.datetime.now()}")
    try:  # <-- must be here

        headers = {
            'Accept': 'application/json'
        }

        r = requests.get('https://api.india.delta.exchange/v2/tickers/BTCUSD', params={

        }, headers=headers)

        # print(r.json()['result']['spot_price'])
        spotPrice = r.json()['result']['spot_price']
        url = "http://0.0.0.0:5000/send-notification"

        payload = json.dumps({
            "spotPrice": spotPrice,
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
    except Exception as e:  # <-- must align with try:
        print("Error calling API:", e)

scheduler.init_app(app)
scheduler.start()



app.register_blueprint(positions_app)
app.register_blueprint(alerts_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


