# -*- encoding: utf-8 -*-
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
    def test_create_and_pasre_url(self):
        params = {
            "transport": "amqp",
            "host": "my.host",
            "port": 4672,
            "username": "guest_user",
            "password": "guest_pwd",
            "virtual_host": "vhost"}
        url = utils.create_url(**params)
        params_ = utils.parse_url(url)
        self.assertEqual(params, params_)

        url_ = utils.create_url(**params_)
        self.assertEqual(url, url_)


if __name__ == '__main__':
    unittest.main()
