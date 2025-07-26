import pymysql # Library to connect Python to MySQL

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='7Suhani$$',
    db='TrainBookingDB',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor() # Used to execute SQL queries
