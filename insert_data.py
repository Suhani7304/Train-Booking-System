import pymysql
import csv
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    db='TrainBookingDB'
)

cursor = conn.cursor()

with open(r"C:\Users\abcde\Downloads\train_routes.csv", 'r') as file:
    reader = csv.reader(file) #creates a csv reader.. each row is list of string
    next(reader)  # Skip header

    # 3. Insert Query
    insert_query = """
    INSERT INTO Route (TrainID, Route)
    VALUES (%s, %s)  
    """ # %s corresponds to the value we will insert

    for row in reader:
        cursor.execute(insert_query, row)

with open(r"C:\Users\abcde\Downloads\train_dataset.csv", 'r') as file:
    reader = csv.reader(file) #creates a csv reader.. each row is list of string
    next(reader)  # Skip header

    # 3. Insert Query
    insert_query = """
    INSERT INTO train (ID, TrainID, TrainName, Source, Destination, ArrivalTime, DepartureTime, Price)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
    """ # %s corresponds to the value we will insert

    for row in reader:
        cursor.execute(insert_query, row)

with open(r"C:\Users\abcde\Downloads\train_seats.csv", 'r') as file:
    reader = csv.reader(file) #creates a csv reader.. each row is list of string
    next(reader)  # Skip header

    # 3. Insert Query
    insert_query = """
    INSERT INTO Admin (ID, UserName, Age, Email, PhoneNumber, Password)
    VALUES (%s, %s, %s, %s, %s, %s) 
    """ # %s corresponds to the value we will insert

    for row in reader:
        cursor.execute(insert_query, row)

with open(r"C:\Users\abcde\Downloads\admin_dataset.csv", 'r') as file:
    reader = csv.reader(file) #creates a csv reader.. each row is list of string
    next(reader)  # Skip header

    # 3. Insert Query
    insert_query = """
    INSERT INTO Seats (SeatID, TrainID, SeatType, TotalSeats)
    VALUES (%s, %s, %s, %s) 
    """ # %s corresponds to the value we will insert

    for row in reader:
        cursor.execute(insert_query, row)


conn.commit()
conn.close()