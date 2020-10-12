import pika
import psycopg2
import time
import os


con = psycopg2.connect(
    host='database',
    database='users',
    user='postgres',
    password='example'
)

cur = con.cursor()

cur.execute("CREATE TABLE Products(Id INTEGER PRIMARY KEY, Name VARCHAR(20), Price INT)")


con.commit()
con.close()  
