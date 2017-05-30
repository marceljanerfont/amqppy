# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import json
import time
import threading
import logging

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
import amqppy
from amqppy import utils
from amqppy.publisher import Topic, Rpc
from amqppy.consumer import Worker


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_publisher = logging.getLogger('amqppy.publisher')
logger_publisher.addHandler(handler)
logger_publisher.setLevel(logging.DEBUG)

logger_consumer = logging.getLogger('amqppy.consumer')
logger_consumer.addHandler(handler)
logger_consumer.setLevel(logging.DEBUG)

EXCHANGE_TEST = "amqppy.test"
BROKER_TEST = "amqp://guest:guest@localhost:5672//"


class PublisherConsumerTests(unittest.TestCase):
    def test_topic(self):
        condition = threading.Event()

        def callback_topic(exchange, routing_key, headers, body):
            print("*** topic callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))
            condition.set()

        worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic).\
            run_async()

        Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                          routing_key="amqppy.test.topic",
                                          body=json.dumps({'msg': 'hello world!'}))

        condition.wait()
        worker.stop()

    def test_rpc(self):
        def callback_request(exchange, routing_key, headers, body):
            return json.dumps(dict(value="Hello budy!"))

        worker = Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        on_request_callback=callback_request).\
            run_async()

        time.sleep(2)

        rpc_reply = Rpc(broker=BROKER_TEST).request(exchange=EXCHANGE_TEST,
                                                    routing_key="amqppy.test.rpc",
                                                    body=json.dumps({'msg': 'hello world!'}))
        print("*** rpc_reply: {}".format(rpc_reply))

        worker.stop()
    
    def test_rpc_timeout(self):
        def callback_request(exchange, routing_key, headers, body):
            time.sleep(2)
            return json.dumps(dict(value="Hello budy!"))

        worker = Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        on_request_callback=callback_request).run_async()

        self.assertRaises(amqppy.ResponseTimeout,
                          lambda: Rpc(broker=BROKER_TEST).request(exchange=EXCHANGE_TEST,
                                                                  routing_key="amqppy.test.rpc",
                                                                  body=json.dumps({'msg': 'hello world!'}),
                                                                  timeout=1))

        worker.stop()

    def test_many_topics_same_topic_different_exchanges(self):
        condition = threading.Event()

        def callback_topic_one(exchange, routing_key, headers, body):
            print("*** topic ONE callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))

        def callback_topic_two(**kargs):
            print("*** topic TWO callback, {}".format(kargs))
            condition.set()

        # differents exchange, so routing_key can be the same
        worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST + ".1",
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST + ".2",
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic_two).\
            run_async()

        # differents exchange, so routing_key can be the same
        topic = Topic(broker=BROKER_TEST)
        topic.publish(exchange=EXCHANGE_TEST + ".1",
                      routing_key="amqppy.test.topic",
                      body=json.dumps({'msg': 'hello world! 1'}))
        topic.publish(exchange=EXCHANGE_TEST + ".2",
                      routing_key="amqppy.test.topic",
                      body=json.dumps({'msg': 'hello world! 2'}))

        print("waiting..")
        condition.wait()
        print("stopping")
        worker.stop()

    def test_many_topics_same_topic_sameexchanges(self):
        condition = threading.Event()

        def callback_topic_one(exchange, routing_key, headers, body):
            print("*** topic ONE callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))

        def callback_topic_two(**kargs):
            print("*** topic TWO callback, {}".format(kargs))
            condition.set()

        # same exchange, therefore differents routing_key
        worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.1",
                      on_topic_callback=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.2",
                      on_topic_callback=callback_topic_two).\
            run_async()

        topic = Topic(broker=BROKER_TEST)
        topic.publish(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.1",
                      body=json.dumps({'msg': 'hello world! 1'}))
        topic.publish(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.2",
                      body=json.dumps({'msg': 'hello world! 2'}))

        print("waiting..")
        condition.wait()
        print("stopping")
        worker.stop()

    def test_fanout(self):
        condition1 = threading.Event()
        condition2 = threading.Event()

        def callback_worker_one(exchange, routing_key, headers, body):
            print("*** topic at worker ONE callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))
            condition1.set()

        def callback_worker_two(**kargs):
            print("*** topic at worker TWO callback, {}".format(kargs))
            condition2.set()

        # same exchange, same routing_key, differents queues. It can be
        # different workers
        worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_one,
                      queue='amqppy.test.worker.1').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_two,
                      queue='amqppy.test.worker.2').\
            run_async()

        Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                          routing_key="amqppy.test.topic",
                                          body=json.dumps({'msg': 'hello world!'}))

        print("waiting..")
        condition1.wait()
        condition2.wait()
        print("stopping")
        worker.stop()

    def test_round_robin(self):
        condition1 = threading.Event()
        condition2 = threading.Event()

        def callback_worker_one(exchange, routing_key, headers, body):
            print("*** topic at worker ONE callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))
            condition1.set()

        def callback_worker_two(**kargs):
            print("*** topic at worker TWO callback, {}".format(kargs))
            condition2.set()

        # same exchange, same routing_key, same queue. It can be different
        # workers
        worker = Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_one,
                      queue='amqppy.test.worker').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_two,
                      queue='amqppy.test.worker').\
            run_async()

        Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                          routing_key="amqppy.test.topic",
                                          body=json.dumps({'msg': 'hello world1!'}))
        Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                          routing_key="amqppy.test.topic",
                                          body=json.dumps({'msg': 'hello world2!'}))

        print("waiting..")
        condition1.wait()
        condition2.wait()
        print("stopping")
        worker.stop()
    """
    TODO:
        test RPC reply uncaught exception
        test exlusive
        test abort_consume
        test dead_letter
        test empty_worker
        test auto_delete
    """


if __name__ == '__main__':
    unittest.main()
