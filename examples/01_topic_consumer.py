# -*- encoding: utf-8 -*-

import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy
from amqppy import consumer


# firstly, run this
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


def on_topic_status(exchange, routing_key, headers, body):
    print('Received message from topic \'amqppy.publisher.topic.status\': {}'.format(body))


try:
    print('Waiting for publieher topics events, to cancel press ctrl + c')
    # subscribe to a topic: 'amqppy.publisher.topic.status'
    worker = consumer.Worker(broker=BROKER_TEST)
    worker.add_topic(exchange=EXCHANGE_TEST,
                     routing_key='amqppy.publisher.topic.status',
                     request_func=on_topic_status)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()
except KeyboardInterrupt:
    print('Exiting')
