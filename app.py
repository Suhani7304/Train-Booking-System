import pymysql
from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    db='TrainBookingDB'
)

cursor = conn.cursor()

