import pymysql
from flask import Flask

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='7Suhani$$',
    db='TrainBookingDB'
)

cursor = conn.cursor()

with open(r"C:\Users\abcde\Downloads\train_dataset.csv", 'r') as file:
    reader = csv.reader(file) #creates a csv reader.. each row is list of string
    next(reader)  # Skip header

    # 3. Insert Query
    insert_query = """
    INSERT INTO train (TrainID, TrainName, Source, Destination, ArrivalTime, DepartureTime, Price)
    VALUES (%s, %s, %s, %s, %s, %s, %s)  #%s corresponds to the value we will insert
    """

    for row in reader:
        cursor.execute(insert_query, row)