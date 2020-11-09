import pika
import psycopg2
import json
import os
import time
import logging


sleepTime = 20
print(' [*] Sleeping for ', sleepTime, ' seconds.')
time.sleep(sleepTime)


print(' [*] Connecting to server ...')
credentials = pika.PlainCredentials(os.environ['RABBITMQ_DEFAULT_USER'],
                                    os.environ['RABBITMQ_DEFAULT_PASS'])
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='messaging', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='request', durable=True)


print(' [*] Connecting to the database...')
postgres_user = os.environ['POSTGRES_USER']
postgres_password = os.environ['POSTGRES_PASSWORD']

try:
    conn = psycopg2.connect(
        host='db',
        database='weather',
        user=postgres_user,
        password=postgres_password
    )

except (Exception, psycopg2.Error) as error:
    if (connection):
        print("Failed to insert record into users table", error)

cursor = conn.cursor()

# Talking with Messaging
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
            response = {'success': False, 'message': "Unknown action"}
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
    cursor.execute('SELECT * FROM users WHERE email=%s or username=%s;', (email, username))
    if cursor.fetchone() != None:
        response = {'success': False, 'message': 'Username or email already exists'}
    else:
        cursor.execute('INSERT INTO users VALUES (%s, %s, %s, %s, %s);',
                       (username, firstname, lastname, email, hashed))
        conn.commit()
        response = {'success': True}
    return response


def get_hash(data):
    username = data['username']
    logging.info(f"GETHASH request for {username} received")
    cursor.execute('SELECT hash FROM users WHERE username=%s;', (username,))
    row = cursor.fetchone()
    if row is None:
        response = {'success': False}
    else:
        response = {'success': True, 'hash': row[0]}
    return response


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='request', auto_ack=True, on_message_callback=process_request)
channel.start_consuming()
