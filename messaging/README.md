# How to use RabbitMQ Management

## What do I need in docker-compose.yml?

```
messaging:
      image: 'rabbitmq:3.8.8-management'
      ports:
        - 15672:15672
```
You have to specify that you're using the management version and you need to forward port 15672

## How do I get to web interface?

You can get to the web interface by going to http://localhost:15672

## What does it show me?

In the Queues tab under "All queues", it will show you any queues that you have made.

In the connection tab, you will see everyone who is connected to this instance. 
