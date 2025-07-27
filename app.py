import MySQLdb

# Connect to the database
db = MySQLdb.connect(
    host='localhost',
    user='root',
    password='7Suhani$$',
    db='TrainBookingDB'
)

# Create a cursor object to execute queries
cursor = db.cursor()