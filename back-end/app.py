import pika
import time

time.sleep(20)

print("Connecting to messaging service...")
credentials = pika.PlainCredentials('guest','guest')
connection = pika.BlockingConnection(
	pika.ConnectionParameters(
        	host='messaging',
		credentials=credentials
  )
)
