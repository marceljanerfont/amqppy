# -*- encoding: utf-8 -*-
import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy
from amqppy.publisher import Topic


# IMPORTANT: firstly, run 'topic_worker.py'
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'

try:
    # publish my current status
    Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                      routing_key='amqppy.publisher.topic.status',
                                      body='RUNNING')
    print('Topics successfully published.')
except (amqppy.ExchangeNotFound, amqppy.PublishNotRouted):
    print('\'01_topic_consumer.py\' should be running before this.')
