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

# add amqppy path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
from amqppy import publisher, consumer, utils


EXCHANGE_TEST = "amqppy.test"
BROKER_TEST = "amqp://guest:guest@localhost:5672//"


class PublisherConsumerTests(unittest.TestCase):
    def test_topic(self):
        condition = threading.Event()

        def callback_topic(exchange, routing_key, headers, body):
            print("*** topic callback, exchange: {}, routing_key: {}, body: {}, headers: {}".format(
                exchange, routing_key, headers, body))
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

        worker = consumer.Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        request_func=callback_request).run_async()

        rpc_response = publisher.rpc_request(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.rpc",
            body=json.dumps({'msg': 'hello world!'}))
        print("*** rpc_response: {}".format(rpc_response))

        worker.stop()

    def test_rpc_timeout(self):
        def callback_request(exchange, routing_key, headers, body):
            time.sleep(2)
            return json.dumps(dict(value="Hello budy!"))

        worker = consumer.Worker(broker=BROKER_TEST).\
            add_request(exchange=EXCHANGE_TEST,
                        routing_key="amqppy.test.rpc",
                        request_func=callback_request).run_async()

        self.assertRaises(amqppy.ResponseTimeout,
                          lambda: publisher.rpc_request(broker=BROKER_TEST,
                                                        exchange=EXCHANGE_TEST,
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
        worker = consumer.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST + ".1",
                      routing_key="amqppy.test.topic",
                      request_func=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST + ".2",
                      routing_key="amqppy.test.topic",
                      request_func=callback_topic_two).\
            run_async()

        # differents exchange, so routing_key can be the same
        the_publisher = publisher.Publisher(
            utils.create_connection(broker=BROKER_TEST))
        the_publisher.publish(exchange=EXCHANGE_TEST + ".1",
                              routing_key="amqppy.test.topic",
                              body=json.dumps({'msg': 'hello world! 1'}))
        the_publisher.publish(exchange=EXCHANGE_TEST + ".2",
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
        worker = consumer.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.1",
                      request_func=callback_topic_one).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic.2",
                      request_func=callback_topic_two).\
            run_async()

        the_publisher = publisher.Publisher(
            utils.create_connection(broker=BROKER_TEST))
        the_publisher.publish(exchange=EXCHANGE_TEST,
                              routing_key="amqppy.test.topic.1",
                              body=json.dumps({'msg': 'hello world! 1'}))
        the_publisher.publish(exchange=EXCHANGE_TEST,
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
        worker = consumer.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      request_func=callback_worker_one,
                      queue='amqppy.test.worker.1').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      request_func=callback_worker_two,
                      queue='amqppy.test.worker.2').\
            run_async()

        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
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
        worker = consumer.Worker(broker=BROKER_TEST).\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      request_func=callback_worker_one,
                      queue='amqppy.test.worker').\
            add_topic(exchange=EXCHANGE_TEST,
                      routing_key="amqppy.test.topic",
                      request_func=callback_worker_two,
                      queue='amqppy.test.worker').\
            run_async()

        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world1!'}))
        publisher.publish(
            broker=BROKER_TEST,
            exchange=EXCHANGE_TEST,
            routing_key="amqppy.test.topic",
            body=json.dumps({'msg': 'hello world2!'}))

        print("waiting..")
        condition1.wait()
        condition2.wait()
        print("stopping")
        worker.stop()


if __name__ == '__main__':
    unittest.main()
