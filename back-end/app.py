import pika
import psycopg2
import time
import os

postgres_password = os.environ['POSTGRES_PASSWORD']
con = psycopg2.connect(
    host='database',
    databast='example',
    user='postgres',
    password=postgres_password  
)

cur = con.cursor()

cur.execute("CREATE TABLE Products(Id INTEGER PRIMARY KEY, Name VARCHAR(20), Price INT)")


con.commit()
con.close()  
