from decimal import Decimal
from pathlib import Path

from flask import Flask, request, jsonify, Blueprint
import boto3
from botocore.exceptions import ClientError
from flask_cors import CORS
import requests

import config

# app = Flask(__name__)
app = Blueprint('alerts', __name__)
CORS(app)

# Use AWS credentials from config.py
aws_access_key_id = config.AWS_ACCESS_KEY_ID
aws_secret_access_key = config.AWS_SECRET_ACCESS_KEY
aws_region = config.AWS_REGION

dynamodb = boto3.resource(
    'dynamodb',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
table_name = 'crypto_alerts'  # Change this to your DynamoDB table name
table = dynamodb.Table(table_name)  # Change this to your history table name
expo_tokens = []
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
FILE_PATH = Path("token.txt")


@app.route('/alert', methods=['POST'])
def create_position_history():
    data = request.json
    try:
        table.put_item(Item=data)
        return jsonify({'message': 'Item created'}), 201
    except ClientError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/alert/<key>', methods=['GET'])
def get_position(key):
    try:
        response = table.get_item(Key={'id': key})
        item = response.get('Item')
        if item:
            return jsonify(item)
        else:
            return jsonify({'error': 'Item not found'}), 404
    except ClientError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/alert/<key>', methods=['DELETE'])
def delete_position(key):
    try:
        table.delete_item(Key={'id': key})
        return jsonify({'message': 'Item deleted'})
    except ClientError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/alerts', methods=['GET'])
def get_all_positions():
    try:
        response = table.scan()
        items = response.get('Items', [])
        return jsonify(items)
    except ClientError as e:
        return jsonify({'error': str(e)}), 400


@app.route("/register-token", methods=["POST"])
def register_token():
    data = request.get_json()
    token = data.get("token")
    if token and token not in expo_tokens:
        expo_tokens.append(token)
        FILE_PATH.write_text(token, encoding="utf-8")
    return jsonify({"status": "success", "tokens": expo_tokens})


@app.route("/send-notification", methods=["POST"])
def send_notification():
    data = request.get_json()
    spotPrice = data.get("spotPrice")
    # print("spotPrice", spotPrice)

    messages = []
    content = FILE_PATH.read_text(encoding="utf-8")
    response = table.scan()
    items = response.get('Items', [])
    for item in items:
        if item.get('symbol') == "below" and float(item.get('text').strip()) > float(spotPrice.strip()):
            messages.append({
                "to": content,
                "sound": "default",
                "title": "BTC crossed below - " + item.get('text').strip(),
                "body": "Current BTC Price - " + spotPrice,
                "data": "{}"
            })
        elif item.get('symbol') == "above" and float(item.get('text').strip()) < float(spotPrice.strip()):
            messages.append({
                "to": content,
                "sound": "default",
                "title": "BTC crossed above - " + item.get('text').strip(),
                "body": "Current BTC Price - " + spotPrice,
                "data": "{}"
            })

    responses = []
    for msg in messages:
        resp = requests.post(EXPO_PUSH_URL, json=msg)
        responses.append(resp.json())

    return jsonify({"status": "sent", "responses": responses})


def send_scheduled_notification(title, body, extra_data):
    print("calling send_scheduled_notification")
    messages = []
    content = FILE_PATH.read_text(encoding="utf-8")
    messages.append({
        "to": content,
        "sound": "default",
        "title": title,
        "body": body,
        "data": extra_data
    })

    responses = []
    for msg in messages:
        resp = requests.post(EXPO_PUSH_URL, json=msg)
        responses.append(resp.json())
        return responses
