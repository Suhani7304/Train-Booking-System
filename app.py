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
def get_cursor():
    conn = pymysql.connect(
        host='localhost',
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        db='TrainBookingDB',
        cursorclass=pymysql.cursors.DictCursor  #get_cursor()), fetchone(), fetchall() returns a dictionary
    )
    return conn, conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_trains():
    if request.method == 'GET':
        conn, cursor = get_cursor()
        cursor.execute("SELECT Route FROM Route")
        routes = cursor.fetchall()

        sources = set()
        destinations = set()

        for r in routes:
            route_string = r['Route']
            stations = [s.strip() for s in route_string.split('->')]
            if len(stations) >= 2:
                sources.update(stations[:-1])       # All except last
                destinations.update(stations[1:])   # All except first

        cursor.close()
        conn.close()

        return render_template('search_form.html',
                               source_stations=sorted(sources),
                               destination_stations=sorted(destinations))
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        conn, cursor = get_cursor()  # can run sql queries here

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
                if row['Destination'].lower() == destination.lower() and src_index != -1 and i >= src_index:
                    dest_index = i
                    break
            if src_index != -1 and dest_index != -1:
                segment = stops[src_index:dest_index+1]
                general = sum([seg['Price'] for seg in segment])
                sleeper = general + 50
                ac3 = general + 200
                ac2 = general + 300
                ac1 = general + 500
                chair_car = general + 100
                train_info = {
                    'train_id': tid,
                    'train_name': stops[0]['TrainName'],
                    'source': source,
                    'destination': destination,
                    'arrival': stops[src_index]['ArrivalTime'],
                    'departure': stops[src_index]['DepartureTime'],
                    'CC': chair_car,
                    'SL': sleeper,
                    'A1': ac1,
                    'A2': ac2,
                    'A3': ac3,
                }
                cursor.execute("SELECT Route FROM Route WHERE TrainID = %s", (tid,))
                route_data = cursor.fetchone()
                if route_data:
                    train_info['route'] = route_data['Route']
                train_data.append(train_info)
        cursor.close()
        conn.close()

        return render_template('search_trains.html', trains=train_data, source=source, destination=destination)
    return redirect(url_for('index'))

@app.route('/book', methods=['POST'])
def book_train():
    data = request.form.to_dict()
    return render_template('book_form.html', data=data)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    data = request.form.to_dict()

    name = data.get("name")
    age = int(data.get("age"))
    gender = data.get("gender")
    email = data.get("email")
    password = data.get("password")
    seat_type = data.get("seat_type")
    travel_date = data.get("date")
    train_id = int(data.get("train_id"))
    source = data.get("source")
    destination = data.get("destination")
    price = float(data.get("price"))
    booking_time = datetime.now()

    conn, cursor = get_cursor()

    # 1. Insert or get Passenger
    cursor.execute("SELECT PassengerID FROM Passenger WHERE Email=%s AND PassengerName=%s", (email, name))
    result = cursor.fetchone()
    if result:
        passenger_id = result['PassengerID']
        print("passenger found")
    else:
        cursor.execute("""
            INSERT INTO Passenger (PassengerName, Age, Gender, Email, Password)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, age, gender, email, password))
        passenger_id = cursor.lastrowid

    # 2. Get SeatID and TotalSeats
    cursor.execute("SELECT SeatID, TotalSeats FROM Seats WHERE TrainID=%s AND SeatType=%s", (train_id, seat_type))
    seat = cursor.fetchone()
    if seat:
        seat_id, total_seats = seat['SeatID'], int(seat['TotalSeats'])
        # Check availability
        cursor.execute("""
            SELECT AvailabilityID, LeftSeats FROM SeatAvailability
            WHERE SeatID=%s AND TravelDate=%s AND Source=%s AND Destination=%s
        """, (seat_id, travel_date, source, destination))
        available = cursor.fetchone()

        if available:
            availability_id, left = available
            if left <= 0:
                flash("Booking failed: No seats left.")
                conn.rollback()
                cursor.close()
                conn.close()
                return redirect(url_for('index'))
            cursor.execute("UPDATE SeatAvailability SET LeftSeats=%s WHERE AvailabilityID=%s", (left - 1, availability_id))
        else:
            cursor.execute("""
                INSERT INTO SeatAvailability (SeatID, TravelDate, Source, Destination, LeftSeats)
                VALUES (%s, %s, %s, %s, %s)
            """, (seat_id, travel_date, source, destination, int(total_seats) - 1))
    else:
        flash("Error: Seat info not found.")
        return redirect(url_for('index'))

    # 3. Insert into Booking
    cursor.execute("""
        INSERT INTO Booking (PassengerID, TrainID, SeatType, TravelDate, Source, Destination, BookingTime, Price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (passenger_id, train_id, seat_type, travel_date, source, destination, booking_time, price))

    conn.commit() 
    cursor.close()
    conn.close()

    pdf_bytes = generate_ticket_pdf(data)
    pdf_bytes.seek(0)
    return send_file(
        pdf_bytes,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{name}_ticket.pdf"
    )


if __name__ == '__main__':
    app.run(debug=True)

