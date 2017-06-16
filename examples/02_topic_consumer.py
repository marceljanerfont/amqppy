# -*- encoding: utf-8 -*-

import sys
import os
import json

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy


# firstly, run this
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


def on_topic_datetime(exchange, routing_key, headers, body):
    print('Received event \'amqppy.publisher.topic.datetime\': {}'.format(json.loads(body)))


def on_topic_status(exchange, routing_key, headers, body):
    print('Received event \'amqppy.publisher.topic.status\': {}'.format(json.loads(body)))


def on_topic_all(exchange, routing_key, headers, body):
    print('Received (*) event \'{}\': {}'.format(routing_key, json.loads(body)))


try:
    print('Waiting for publieher topics events, to cancel press ctrl + c')
    worker = amqppy.Worker(broker=BROKER_TEST).\
        add_topic(exchange=EXCHANGE_TEST,
                  routing_key="amqppy.publisher.topic.datetime",
                  on_topic_callback=on_topic_datetime).\
        add_topic(exchange=EXCHANGE_TEST,
                  routing_key="amqppy.publisher.topic.status",
                  on_topic_callback=on_topic_status).\
        add_topic(exchange=EXCHANGE_TEST,
                  routing_key="amqppy.publisher.topic.*",
                  on_topic_callback=on_topic_all).\
        run()
except KeyboardInterrupt:
    worker.stop()
    print('Exiting')
