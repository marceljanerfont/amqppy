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

        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic).\
            run_async()
        try:
            amqppy.Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                                     routing_key="amqppy.test.topic",
                                                     body=json.dumps({'msg': 'hello world!, नमस्कार संसार'}))

            condition.wait()
        finally:
            worker.stop()

    def test_rpc_echo(self):
        def callback_request(exchange, routing_key, headers, body):
            return body

        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        on_request_callback=callback_request).\
            run_async()
        try:
            message = json.dumps({'msg': 'hello world!, नमस्कार संसार'})

            rpc_reply = amqppy.Rpc(broker=BROKER_TEST).request(exchange=EXCHANGE_TEST,
                                                               routing_key="amqppy.test.rpc",
                                                               body=message)
            print("*** rpc_reply: {}".format(rpc_reply))
            self.assertEqual(message, rpc_reply)
        finally:
            worker.stop()

    def test_rpc_timeout(self):
        def callback_request(exchange, routing_key, headers, body):
            time.sleep(2)
            return json.dumps(dict(value="Hello budy!"))

        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        on_request_callback=callback_request).run_async()
        try:
            self.assertRaises(amqppy.ResponseTimeout,
                              lambda:
                              amqppy.Rpc(broker=BROKER_TEST).request(exchange=EXCHANGE_TEST,
                                                                     routing_key="amqppy.test.rpc",
                                                                     body=json.dumps({'msg': 'hello world!, नमस्कार संसार'}),
                                                                     timeout=1))
        finally:
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
        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST + ".1",
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST + ".2",
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_topic_two).\
            run_async()
        try:
            # differents exchange, so routing_key can be the same
            topic = amqppy.Topic(broker=BROKER_TEST)
            topic.publish(exchange=EXCHANGE_TEST + ".1",
                          routing_key="amqppy.test.topic",
                          body=json.dumps({'msg': 'hello world! 1'}))
            topic.publish(exchange=EXCHANGE_TEST + ".2",
                          routing_key="amqppy.test.topic",
                          body=json.dumps({'msg': 'hello world! 2'}))
            condition.wait()
        finally:
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
        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.1",
                      on_topic_callback=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.2",
                      on_topic_callback=callback_topic_two).\
            run_async()

        try:
            topic = amqppy.Topic(broker=BROKER_TEST)
            topic.publish(exchange=EXCHANGE_TEST,
                          routing_key="amqppy.test.topic.1",
                          body=json.dumps({'msg': 'hello world! 1'}))
            topic.publish(exchange=EXCHANGE_TEST,
                          routing_key="amqppy.test.topic.2",
                          body=json.dumps({'msg': 'hello world! 2'}))

            condition.wait()
        finally:
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
        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_one,
                      queue='amqppy.test.worker.1').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_two,
                      queue='amqppy.test.worker.2').\
            run_async()
        try:
            amqppy.Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                                     routing_key="amqppy.test.topic",
                                                     body=json.dumps({'msg': 'hello world!, नमस्कार संसार'}))
            condition1.wait()
            condition2.wait()
        finally:
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
        worker = amqppy.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_one,
                      queue='amqppy.test.worker').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      on_topic_callback=callback_worker_two,
                      queue='amqppy.test.worker').\
            run_async()
        try:
            amqppy.Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                                     routing_key="amqppy.test.topic",
                                                     body=json.dumps({'msg': 'hello world1!, नमस्कार संसार'}))
            amqppy.Topic(broker=BROKER_TEST).publish(exchange=EXCHANGE_TEST,
                                                     routing_key="amqppy.test.topic",
                                                     body=json.dumps({'msg': 'hello world2!, नमस्कार संसार'}))
            condition1.wait()
            condition2.wait()
        finally:
            worker.stop()

    """
    TODO:
        test RPC reply uncaught exception
        test auto_delete
        test abort_consume
        test dead_letter
    """


if __name__ == '__main__':
    unittest.main()
