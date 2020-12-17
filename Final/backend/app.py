import pika
import psycopg2
import os
import time
import logging
import json

# tag::process_request[]
def process_request(ch, method, properties, body):
    """
    Gets a request from the queue, acts on it, and returns a response to the
    reply-to queue
    """
    request = json.loads(body)
    if 'action' not in request:
        response = {
            'success': False,
            'message': "Request does not have action"
        }
    else:
        action = request['action']
        if action == 'GETHASH':
            data = request['data']
            email = data['email']
            logging.info(f"GETHASH request for {email} received")
            curr_r.execute('SELECT hash FROM users WHERE email=%s;', (email,))
            row =  curr_r.fetchone()
            if row == None:
                response = {'success': False}
            else:
                response = {'success': True, 'hash': row[0]}
        elif action == 'REGISTER':
            data = request['data']
            email = data['email']
            hashed = data['hash']
            logging.info(f"REGISTER request for {email} received")
            curr_r.execute('SELECT * FROM users WHERE email=%s;', (email,))
            if curr_r.fetchone() != None:
                response = {'success': False, 'message': 'User already exists'}
            else:
                curr_rw.execute('INSERT INTO users VALUES (%s, %s);', (email, hashed))
                conn_rw.commit()
                response = {'success': True}
        else:
            response = {'success': False, 'message': "Unknown action"}
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)
    )
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
# tag::updated_db[]
        logging.info("Connecting to the read-only database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        conn_r = psycopg2.connect(
            host='db-r',
            database='example',
            user='postgres',
            password=postgres_password
        )

        logging.info("Connecting to the read-write database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        conn_rw = psycopg2.connect(
            host='db-rw',
            database='example',
            user='postgres',
            password=postgres_password
        )
# end::updated_db[]

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

curr_r = conn_r.cursor()
curr_rw = conn_rw.cursor()
channel = connection.channel()

# create the request queue if it doesn't exist
channel.queue_declare(queue='request')

channel.basic_consume(queue='request', auto_ack=True,
                      on_message_callback=process_request)

# loops forever consuming from 'request' queue
logging.info("Starting consumption...")
channel.start_consuming()
