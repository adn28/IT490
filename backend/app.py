import pika
import psycopg2
import os
import time
import logging
import json

# tag::process_request[]
def process_request(ch, method, properties, body):

    request = json.loads(body)
    if 'action' not in request:
        response = {
            'success': False,
            'message': "Request does not have action"
        }
    else:
        action = request['action']
        data = request['data']
        if action == 'GETHASH':
            response = get_hash(data)
        elif action == 'REGISTER':
            response = register_user(data)
        else:
            response = {'success' : False, 'message': "Unknown action"}
    
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)

)

def register_user(data):
    firstname = data['firstname']
    lastname = data['lastname']
    email = data['email']
    username = data['username']
    hashed = data['hash']
    logging.info(f"REGISTER request for {email} received")
    curr_r.execute('SELECT * FROM users WHERE email=%s or username=%s;', (email, username))
    if curr_r.fetchone() != None:
        response = {'success': False, 'message': 'Username or email already exists'}
    else:
        curr_rw.execute('INSERT INTO users VALUES (%s, %s, %s, %s, %s);',
                       (username, firstname, lastname, email, hashed))
        conn.commit()
        response = {'success': True}
    return response

def get_hash(data):
    username = data['username']
    logging.info(f"GETHASH rquest for{username} received")
    curr_r.execute('SELECT has FROM users WHERE username=%s;', (username,))
    row = curr_r.fetchone()
    if row is None:
        response = {'success' : False}
    else:
        response = {'success' : True, 'hash' : row[0]}
    return response

# end::process_request[]



logging.basicConfig(level=logging.INFO)

# repeatedly try to connect to db and messaging, waiting up to 60s, doubling
# backoff

wait_time = 1
while True:
    logging.info(f"Waiting {wait_time}s...")
    time.sleep(wait_time)
    if wait_time < 60:
        wait_time = wait_time * 2
    else:
        wait_time = 60
    try:
        logging.info("Connecting to the read and write database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        postgres_user = os.environ['POSTGRES_USER']
        conn_rw = psycopg2.connect(
            host="db1, db2",
            database="weather",
            user=postgres_user,
            password=postgres_password
            
        )

        logging.info("Connecting to the read database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        postgres_user = os.environ['POSTGRES_USER']
        conn_r = psycopg2.connect(
            host="db2, db1",
            database="weather",
            user=postgres_user,
            password=postgres_password
        
        )


        logging.info("Connecting to messaging service...")
        credentials = pika.PlainCredentials(
            os.environ['RABBITMQ_DEFAULT_USER'],
            os.environ['RABBITMQ_DEFAULT_PASS']
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='messaging',
                credentials=credentials
            )
        )

        break
    except psycopg2.OperationalError:
        print(f"Unable to connect to database.")
        continue
    except pika.exceptions.AMQPConnectionError:
        print("Unable to connect to messaging.")
        continue
cur_r = conn_r.cursor()
cur_rw = conn_rw.cursor()
channel = connection.channel()

# create the request queue if it doesn't exist
channel.queue_declare(queue='request')

channel.basic_consume(queue='request', auto_ack=True, on_message_callback=process_request)

# loops forever consuming from 'request' queue
logging.info("Starting consumption...")
channel.start_consuming()
