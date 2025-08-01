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
            availability_id, left = available['AvailabilityID'], available['LeftSeats']
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
        INSERT INTO Booking (PassengerID, TrainID, SeatType, TravelDate, Source, Destination, BookingTime, Price, Status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (passenger_id, train_id, seat_type, travel_date, source, destination, booking_time, price, "Confirmed"))

    conn.commit() 
    cursor.close()
    conn.close()
    return render_template("book_form.html", confirmed=True, data=data)

@app.route('/download_ticket', methods=['POST'])
def download_ticket():
    data = request.form.to_dict()
    pdf_bytes = generate_ticket_pdf(data)
    pdf_bytes.seek(0)
    return send_file(
        pdf_bytes,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{data['name']}_ticket.pdf"
    )


@app.route('/view_cancel', methods=['GET', 'POST'])
def view_cancel():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn, cursor = get_cursor()

        cursor.execute("SELECT * FROM Passenger WHERE PassengerName=%s AND Email=%s", (name, email))
        passenger = cursor.fetchone()

        if not passenger or passenger['Password'] != password:
            flash('Invalid credentials!')
            return redirect('/view_cancel')

        passenger_id = passenger['PassengerID']
        cursor.execute("""
            SELECT DISTINCT 
                b.BookingID, b.BookingTime, b.TravelDate, b.Source, b.Destination, 
                b.SeatType, b.Status, b.Price, 
                t.TrainID, t.TrainName, t.ArrivalTime, t.DepartureTime
            FROM Booking b
            JOIN Train t ON b.TrainID = t.TrainID AND t.Source = b.Source
            WHERE b.PassengerID = %s
        """, (passenger_id,))
        bookings = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template('show_bookings.html', bookings=bookings, passenger_id=passenger_id)

    return render_template('view_cancel.html')

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    
    conn, cursor = get_cursor()

    # Get booking details
    cursor.execute("SELECT * FROM Booking WHERE BookingID = %s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        return jsonify({'status': 'error', 'message': 'Booking not found'})

    train_id = booking['TrainID']
    travel_date = booking['TravelDate']
    coach_type = booking['SeatType']

    # Delete the booking
    cursor.execute("UPDATE Booking SET Status = 'Cancelled' WHERE BookingID = %s", (booking_id,))

    # Increment seat count in SeatAvailability
    cursor.execute("SELECT SeatID FROM Seats WHERE TrainID = %s AND SeatType = %s", (train_id, coach_type))
    seat_row = cursor.fetchone()

    seat_id = seat_row['SeatID']

    # Step 2: Use seat_id, travel_date, source, destination to update SeatAvailability
    cursor.execute("""
        UPDATE SeatAvailability 
        SET LeftSeats = LeftSeats + 1
        WHERE SeatID = %s AND TravelDate = %s AND Source = %s AND Destination = %s
    """, (seat_id, travel_date, booking['Source'], booking['Destination']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cursor = get_cursor()
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        cursor.close()
        conn.close()
        if cursor.fetchone():
            return redirect(url_for('admin_dashboard'))
        flash("Invalid credentials")
        return redirect('/admin_login')
    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    conn, cursor = get_cursor()
    cursor.execute("""
        SELECT t.TrainID, t.TrainName,
        GROUP_CONCAT(DISTINCT r.Route ORDER BY r.Route SEPARATOR ' -> ') AS Route
        FROM train t JOIN Route r ON t.TrainID = r.TrainID
        GROUP BY t.TrainID, t.TrainName
    """)
    trains = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', trains=trains)


@app.route('/train_form', defaults={'train_id': None}, methods=['GET', 'POST'])
@app.route('/train_form/<train_id>', methods=['GET', 'POST'])
def train_form(train_id):
    conn, cursor = get_cursor()
    if request.method == 'POST':
        train_id_input = request.form['train_id']
        train_name = request.form['train_name']
        price = request.form['price']
        route = [x.strip() for x in request.form['route'].split(',')]

        # DELETE OLD DATA IF EDIT
        if train_id:
            cursor.execute("DELETE FROM train WHERE TrainID=%s", (train_id,))
            cursor.execute("DELETE FROM Route WHERE TrainID=%s", (train_id,))
            cursor.execute("DELETE FROM Seats WHERE TrainID=%s", (train_id,))

        route_str = " -> ".join(route)  # Join stations into one string
        cursor.execute("INSERT INTO Route (TrainID, Route) VALUES (%s, %s)", (train_id_input, route_str))

        # INSERT INTO train
        for i in range(len(route) - 1):
            arr = request.form.get(f'arrival_time_{i}', '')
            dep = request.form.get(f'departure_time_{i}', '')
            cursor.execute("SELECT MAX(ID) FROM train")
            result = cursor.fetchone()
            max_id = list(result.values())[0] if result and list(result.values())[0] is not None else 0
            new_id = max_id + 1

            cursor.execute("""
                INSERT INTO train (ID, TrainID, TrainName, Source, Destination, ArrivalTime, DepartureTime, Price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id, train_id_input, train_name, route[i], route[i + 1], arr, dep, price))


        # INSERT INTO seats
        for seat_type in ['Chair Car (CC)', 'First AC (1A)', 'Second AC (2A)', 'Third AC (3A)']:
            total = request.form.get(f'seat_{seat_type}')
            cursor.execute("SELECT MAX(SeatID) FROM Seats")
            result = cursor.fetchone()
            max_id = list(result.values())[0] if result and list(result.values())[0] is not None else 0
            new_id = max_id + 1
            if total:
                cursor.execute("""
                    INSERT INTO seats (SeatID, TrainID, SeatType, TotalSeats)
                    VALUES (%s, %s, %s, %s)
                """, (new_id, train_id_input, seat_type, total))

        conn.commit()
        return redirect('/admin_dashboard')

    # GET method (Edit)
    train = None
    route_str = None
    seats = {}
    if train_id:
        cursor.execute("SELECT * FROM train WHERE TrainID=%s", (train_id,))
        train = cursor.fetchone()
        cursor.execute("SELECT Route FROM Route WHERE TrainID=%s", (train_id,))
        row = cursor.fetchone()
        route_str = row['Route'].replace('->', ',') if row else ''
        cursor.execute("SELECT SeatType, TotalSeats FROM Seats WHERE TrainID=%s", (train_id,))
        seats = {row['SeatType']: row['TotalSeats'] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return render_template("train_form.html", train=train, route_str=route_str, seats=seats)


@app.route('/delete_train/<train_id>', methods=['POST'])
def delete_train(train_id):
    conn, cursor = get_cursor()
    cursor.execute("DELETE FROM train WHERE TrainID = %s", (train_id,))
    cursor.execute("DELETE FROM Seats WHERE TrainID = %s", (train_id,))
    cursor.execute("DELETE FROM Route WHERE TrainID = %s", (train_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin_dashboard')


if __name__ == '__main__':
    app.run(debug=True)

