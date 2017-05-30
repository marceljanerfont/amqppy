# -*- encoding: utf-8 -*-
import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import amqppy
from amqppy.publisher import Rpc


# IMPORTANT: firstly, run 'rpc_consumer.py'
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'

try:
    # publish my current status
    result = Rpc(broker=BROKER_TEST).request(exchange=EXCHANGE_TEST,
                                             routing_key='amqppy.requester.rpc.fib',
                                             body='10')
    print('Rpc successfully replyed, resuklt: {}.'.format(result))
except (amqppy.ExchangeNotFound, amqppy.PublishNotRouted):
    print('\'01_rpc_consumer.py\' should be running before this.')
