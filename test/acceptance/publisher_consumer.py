# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import json
import threading
import time
# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
from amqppy import publisher, consumer


EXCHANGE_TEST = "amqppy.test"
BROKER_TEST = "amqp://guest:guest@localhost:5672//"


class PublisherConsumerTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_topic(self):
        condition = threading.Event()
        def callback_topic(routing_key, body, headers):
            print("*** topic callback, routing_key: {}, body: {}, headers: {}".format(routing_key, body, headers))
            condition.set()

            
        worker = consumer.Worker(broker=BROKER_TEST)
        worker.add_topic(
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.topic",
            request_func=callback_topic)

        worker.run_async()

        publisher.publish(
            broker=BROKER_TEST,
            exchange="amqppy.test",
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world!'}))

        condition.wait()
        worker.stop()


    def test_rpc(self):
        def callback_request(routing_key, body, headers):
            return json.dumps(dict(value="Hello budy!"))

        worker = consumer.Worker(broker=BROKER_TEST).add_request(exchange=EXCHANGE_TEST,
                                                                 routing_key="amqppy.test.rpc",
                                                                 request_func=callback_request)

        worker.run_async()

        rpc_response = publisher.rpc_request(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.rpc",
            body=json.dumps({'msg': 'hello world!'}))
        print("*** rpc_response: {}".format(rpc_response))

        worker.stop()


    def tearDown(self):
        pass




if __name__ == '__main__':
    unittest.main()