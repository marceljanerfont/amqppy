# -*- encoding: utf-8 -*-

import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from amqppy.consumer import Worker


# firstly, run this
# AMQP Exchange should be of type 'topic'

EXCHANGE_TEST = 'amqppy.test'
BROKER_TEST = 'amqp://guest:guest@localhost:5672//'


def fib(n):
    if n <= 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


def on_rpc_request(exchange, routing_key, headers, body):
    print("RPC request: {}, body: {}".format(routing_key, body))
    return fib(int(body))


try:
    print('Waiting for RPC requst, to cancel press ctrl + c')
    # subscribe to a rpc request: 'amqppy.requester.rpc.fib'
    worker = Worker(broker=BROKER_TEST)
    worker.add_request(exchange=EXCHANGE_TEST,
                       routing_key='amqppy.requester.rpc.fib',
                       on_request_callback=on_rpc_request)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()
except KeyboardInterrupt:
    print('Exiting')
