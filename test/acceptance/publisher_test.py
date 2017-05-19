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


"""TODO:
    publish no route
    publish ok
    rpc no routed
    rpc timout
    rpc ok
"""
class PublishTests(unittest.TestCase):
    def test_publish_not_routed(self):
        try:
            publisher.publish(
                broker="amqp://guest:guest@localhost:5672//",
                exchange="amqppy.test",
                routing_key="amqppy.test.publish.ok",
                body=json.dumps({'msg': 'hello world!'}))
        except amqppy.PublishNotRouted:
            pass


class RpcTests(unittest.TestCase):
    def test_rpc_not_routed(self):
        try:
            publisher.rpc_request(
                broker="amqp://guest:guest@localhost:5672//",
                exchange="amqppy.test",
                routing_key="amqppy.test.publish.ok",
                body=json.dumps({'msg': 'hello world!'}))
        except amqppy.PublishNotRouted:
            pass
        except amqppy.ResponseTimeout:
            pass

if __name__ == '__main__':
    unittest.main()