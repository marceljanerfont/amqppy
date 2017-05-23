# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import json

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
from amqppy import publisher, utils


EXCHANGE_TEST = "amqppy.test"
BROKER_TEST = "amqp://guest:guest@localhost:5672//"


class NotRoutedTest(unittest.TestCase):
    def setUp(self):
        # creates exchange
        self.connection = utils.create_connection(broker=BROKER_TEST)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EXCHANGE_TEST, exchange_type="topic",
                                      passive=False, durable=True, auto_delete=True)

    def tearDown(self):
        self.channel.exchange_delete(exchange=EXCHANGE_TEST)
        self.channel.close()
        self.connection.close()

    def test_not_routed(self):
        self.assertRaises(amqppy.PublishNotRouted,
                          lambda: publisher.publish(broker=BROKER_TEST,
                                                    exchange=EXCHANGE_TEST,
                                                    routing_key="amqppy.test.topic",
                                                    body=json.dumps({'msg': 'hello world!'})))


class ExchangeNotFoundTest(unittest.TestCase):
    def setUp(self):
        # ensure that exchange doesn't exist
        self.connection = utils.create_connection(broker=BROKER_TEST)
        self.channel = self.connection.channel()
        exist = False
        try:
            self.channel.exchange_declare(exchange=EXCHANGE_TEST, exchange_type="topic", passive=True)
            exist = True
        except Exception:
            pass
        if exist:
            raise Exception("Exchange {} should not exist for this test".format(EXCHANGE_TEST))

    def tearDown(self):
        self.connection.close()

    def test_exchange_not_found(self):
        self.assertRaises(amqppy.ExchangeNotFound,
                          lambda: publisher.publish(broker=BROKER_TEST,
                                                    exchange=EXCHANGE_TEST,
                                                    routing_key="amqppy.test.topic",
                                                    body=json.dumps({'msg': 'hello world!'})))


if __name__ == '__main__':
    unittest.main()