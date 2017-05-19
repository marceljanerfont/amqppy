try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from amqppy import utils


class UtilsTests(unittest.TestCase):

    def test_create_url_without_virtual_host(self):
        url = utils.create_url(
            host="rabbit.host",
            port=5673,
            username="serviceuser",
            password="password")
        self.assertEqual(url, "amqp://serviceuser:password@rabbit.host:5673//")

    def test_create_url_with_virtual_host(self):
        url = utils.create_url(virtual_host="vhost")
        self.assertEqual(url, "amqp://guest:guest@localhost:5672/vhost")

    def test_parse_url_without_virtual_host(self):
        params = utils.parse_url("amqp://serviceuser:password@rabbit.host:5673//")
        self.assertEqual(params["transport"], "amqp")
        self.assertEqual(params["host"], "rabbit.host")
        self.assertEqual(params["port"], 5673)
        self.assertEqual(params["username"], "serviceuser")
        self.assertEqual(params["password"], "password")
        self.assertEqual(params["virtual_host"], "/")

    def test_parse_url_with_virtual_host(self):
        params = utils.parse_url("amqp://guest:guest@localhost:5672/vhost")
        self.assertEqual(params["transport"], "amqp")
        self.assertEqual(params["host"], "localhost")
        self.assertEqual(params["port"], 5672)
        self.assertEqual(params["username"], "guest")
        self.assertEqual(params["password"], "guest")
        self.assertEqual(params["virtual_host"], "vhost")


if __name__ == '__main__':
    unittest.main()
