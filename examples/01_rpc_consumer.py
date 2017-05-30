# -*- encoding: utf-8 -*-

import sys
import os
import json

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from amqppy.consumer import Worker


# firstly, run this
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


def on_rpc_request_division(exchange, routing_key, headers, body):
    print("RPC request: {}, body: {}".format(routing_key, body))
    args = json.loads(body)
    return args['dividend'] / args['divisor']


try:
    print('Waiting for RPC requst, to cancel press ctrl + c')
    # subscribe to a rpc request: 'amqppy.requester.rpc.division'
    worker = Worker(broker=BROKER_TEST)
    worker.add_request(exchange=EXCHANGE_TEST,
                       routing_key='amqppy.requester.rpc.division',
                       on_request_callback=on_rpc_request_division)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()
except KeyboardInterrupt:
    print('Exiting')
