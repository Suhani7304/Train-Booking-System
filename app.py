import pymysql
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
import os
from dotenv import load_dotenv
from ticket_generator import generate_ticket_pdf
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    db='TrainBookingDB',
    cursorclass=pymysql.cursors.DictCursor
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_trains():
    if request.method == 'GET':
        return render_template('search_form.html')
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        cursor = conn.cursor()  # can run sql queries here

        # Get all train IDs that include both source and destination
        cursor.execute("SELECT * FROM train ORDER BY TrainID, ID")
        all_trains = cursor.fetchall()

        train_data = []
        train_map = {}

        for row in all_trains:
            tid = row['TrainID']
            if tid not in train_map:
                train_map[tid] = []
            train_map[tid].append(row)

        for tid, stops in train_map.items():
            src_index = dest_index = -1
            for i, row in enumerate(stops):
                if row['Source'].lower() == source.lower():
                    src_index = i
                if row['Destination'].lower() == destination.lower() and src_index != -1 and i > src_index:
                    dest_index = i
                    break
            if src_index != -1 and dest_index != -1:
                segment = stops[src_index:dest_index+1]
                total_price = sum([seg['Price'] for seg in segment])
                general = total_price
                sleeper = general + 50
                ac3 = general + 200
                ac2 = general + 300
                ac1 = general + 500
                train_info = {
                    'train_id': tid,
                    'train_name': stops[0]['TrainName'],
                    'source': source,
                    'destination': destination,
                    'arrival': stops[src_index]['ArrivalTime'],
                    'departure': stops[src_index]['DepartureTime'],
                    'general': general,
                    'sleeper': sleeper,
                    'ac1': ac1,
                    'ac2': ac2,
                    'ac3': ac3,
                }
                cursor.execute("SELECT Route FROM route WHERE TrainID = %s", (tid,))
                route_data = cursor.fetchone()
                if route_data:
                    train_info['route'] = route_data['Route']
                train_data.append(train_info)

        return render_template('search_trains.html', trains=train_data, source=source, destination=destination)
    return redirect(url_for('index'))

@app.route('/book', methods=['POST'])
def book_train():
    data = request.form.to_dict()
    return render_template('book_form.html', data=data)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    data = request.form.to_dict()
    generate_ticket_pdf(data)
    flash("Train booked successfully!")
    return render_template('ticket.html', filename='ticket.pdf')

@app.route('/download_ticket/<filename>')
def download_ticket(filename):
    path = os.path.join('static', filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

