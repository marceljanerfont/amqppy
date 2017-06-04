# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import json
import logging

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
from amqppy import utils
from amqppy.consumer import Worker

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_publisher = logging.getLogger('amqppy.publisher')
logger_publisher.addHandler(handler)
logger_publisher.setLevel(logging.DEBUG)

EXCHANGE_TEST = "amqppy.test"
BROKER_TEST = "amqp://guest:guest@localhost:5672//"


"""
TODO:
    test empty_worker
"""


def callback(**kargs):
    print('I am the callback')


class ExclusiveQueueTopic(unittest.TestCase):
    def setUp(self):
        # creates exchange
        self.worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      exclusive=True,
                      on_topic_callback=callback)
        self.worker.run_async()
        self.worker2 = Worker(broker=BROKER_TEST)

    def tearDown(self):
        self.worker.stop()
        self.worker2.stop()

    def test_exclusive(self):
        self.assertRaises(amqppy.ExclusiveQueue,
                          lambda: self.worker2.add_topic(exchange=EXCHANGE_TEST,
                                                         routing_key="amqppy.test.topic",
                                                         on_topic_callback=callback))


class ExclusiveQueueRpc(unittest.TestCase):
    def setUp(self):
        # creates exchange
        self.worker = Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        on_request_callback=callback,
                        exclusive=True).\
            run_async()

        self.worker2 = Worker(broker=BROKER_TEST)

    def tearDown(self):
        self.worker.stop()
        self.worker2.stop()

    def test_exclusive(self):
        self.assertRaises(amqppy.ExclusiveQueue,
                          lambda: self.worker2.add_request(exchange=EXCHANGE_TEST,
                                                           routing_key="amqppy.test.rpc",
                                                           on_request_callback=callback))


if __name__ == '__main__':
    unittest.main()
