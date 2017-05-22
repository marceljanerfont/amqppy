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
    """
    def test_topic(self):
        condition = threading.Event()
        def callback_topic(exchange, routing_key, headers, body):
            print("*** topic callback, exchange: {}, outing_key: {}, body: {}, headers: {}".format(exchange, routing_key, headers, body))
            condition.set()

            
        worker = consumer.Worker(broker=BROKER_TEST)
        worker.add_topic(
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.topic",
            request_func=callback_topic)

        worker.run_async()

        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world!'}))

        condition.wait()
        worker.stop()

    def test_rpc(self):
        def callback_request(exchange, routing_key, headers, body):
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
    """

    def test_many_topics_same_topic_different_exchanges(self):
        condition = threading.Event()
        def callback_topic_one(exchange, routing_key, headers, body):
            print("*** topic ONE callback, exchange: {}, outing_key: {}, body: {}, headers: {}".format(exchange, routing_key, headers, body))
            condition.set()

        def callback_topic_two(**kargs):
            print("*** topic TWO callback, {}".format(kargs))
            condition.set()

            
        worker = consumer.Worker(broker=BROKER_TEST).\
                                add_topic(exchange=EXCHANGE_TEST + ".1",
                                          routing_key="amqppy.test.topic",
                                          request_func=callback_topic_one).\
                                add_topic(exchange=EXCHANGE_TEST + ".2",
                                          routing_key="amqppy.test.topic",
                                          request_func=callback_topic_two)

        worker.run_async()

        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST + ".1",
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world! 1'}))

        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST + ".2",
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world! 2'}))

        print("waiting..")
        condition.wait()
        print("stopping")
        worker.stop()


    def tearDown(self):
        pass




if __name__ == '__main__':
    unittest.main()