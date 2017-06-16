# -*- encoding: utf-8 -*-

import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy


# firstly, run this
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


def on_topic_status(exchange, routing_key, headers, body):
    print('Received message from topic \'amqppy.publisher.topic.status\': {}'.format(body))


try:
    # connect to the broker
    worker = amqppy.Worker(broker=BROKER_TEST)
    # subscribe to a topic: 'amqppy.publisher.topic.status'
    worker.add_topic(exchange=EXCHANGE_TEST,
                     routing_key='amqppy.publisher.topic.status',
                     on_topic_callback=on_topic_status)
    # wait until worker is stopped or an uncaught exception
    print('Waiting for topics events, to cancel press ctrl + c')
    worker.run()
except KeyboardInterrupt:
    worker.stop()
    print('Exiting')
