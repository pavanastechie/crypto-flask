from decimal import Decimal

from flask import Flask, request, jsonify, Blueprint
import boto3
from botocore.exceptions import ClientError
from flask_cors import CORS
import config

# app = Flask(__name__)

app = Blueprint('positions', __name__)
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
table_name = 'crypto_positions'  # Change this to your DynamoDB table name
table = dynamodb.Table(table_name)
history_table = dynamodb.Table('crypto_positions_history')  # Change this to your history table name

@app.route('/position', methods=['POST'])
def create_position():
    data = request.json
    try:
        table.put_item(Item=float_to_decimal(data))
        return jsonify({'message': 'Item created'}), 201
    except ClientError as e:
        return jsonify({'error': str(e)}), 400

def float_to_decimal(obj):
    if isinstance(obj, list):
        return [float_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj



@app.route('/positionHistory', methods=['POST'])
def create_position_history():
    data = request.json
    try:
        history_table.put_item(Item=data)
        return jsonify({'message': 'Item created'}), 201
    except ClientError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/position/<key>', methods=['GET'])
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

@app.route('/position/<key>', methods=['PUT'])
def update_position(key):
    data = request.json
    print("key:", key)
    print("data:", data)
    try:
        table.update_item(
            Key={'id': key},

            UpdateExpression="set lotSize=:ls",
            ExpressionAttributeValues={
                ':ls': data.get('lotSize', '')
            },
            ReturnValues="UPDATED_NEW"
        )
        return jsonify({'message': 'Item updated'})
    except ClientError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/position/<key>', methods=['DELETE'])
def delete_position(key):
    try:
        table.delete_item(Key={'id': key})
        return jsonify({'message': 'Item deleted'})
    except ClientError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/positions', methods=['GET'])
def get_all_positions():
    try:
        response = table.scan()
        items = response.get('Items', [])
        return jsonify(items)
    except ClientError as e:
        return jsonify({'error': str(e)}), 400
