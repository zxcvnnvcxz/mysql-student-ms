import mysql.connector
import os

password = os.getenv("mysql_pw")

def test_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password,
            database="school"
        )
        print("Connection successful!")
        connection.close()
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")

test_connection()
