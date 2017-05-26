# -*- encoding: utf-8 -*-
import sys
import os
import json
import datetime

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy
from amqppy import publisher


# IMPORTANT: firstly, run 'topic_worker.py'
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


try:
    # do all with only one connection
    topic_publisher = publisher.Publisher(broker=BROKER_TEST)
    # publish my current time
    topic_publisher.publish(exchange=EXCHANGE_TEST,
                            routing_key='amqppy.publisher.topic.datetime',
                            body=json.dumps({'datetime': datetime.datetime.now().isoformat()}))
    # publish my current status
    topic_publisher.publish(exchange=EXCHANGE_TEST,
                            routing_key='amqppy.publisher.topic.status',
                            body=json.dumps({'status': 'working'}))
    print('Topics successfully published.')
except (amqppy.ExchangeNotFound, amqppy.PublishNotRouted):
    print('\'02_topic_consumer.py\' should be running before this.')
