# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import json

# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import amqppy
from amqppy import publisher
from amqppy import consumer


"""TODO:
    consumer topic
    consumer rpc
"""
class ConsumerTests(unittest.TestCase):
    def test_consumer_topic(self):
        def callback(routing_key, body, headers):
            print("topic callback, routing_key: {}, body: {}, headers: {}".format(outing_key, body, headers))

        try:
            worker = consumer.Worker(broker="amqp://guest:guest@localhost:5672//")
            worker.add_topic(
                exchange="amqppy.test",
                routing_key="amqppy.test.publish.ok",
                request_func=callback)
            worker.run()
        except amqppy.PublishNotRouted:
            pass




if __name__ == '__main__':
    unittest.main()