# -*- encoding: utf-8 -*-
__version__ = '0.0.5'
DEFAULT_PORT = 5672
AMQP_EXCHANGE = "amqppy"
AMQP_BROKER = "amqp://localhost:{}//".format(DEFAULT_PORT)

# how to publish a package to pypi
# https://packaging.python.org/distributing/

import logging
try:
    # not available in python 2.6
    from logging import NullHandler
except ImportError:

    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

# Add NullHandler to prevent logging warnings
logging.getLogger(__name__).addHandler(NullHandler())


class ResponseTimeout(Exception):
    pass


class PublishNotRouted(Exception):
    pass


class ExchangeNotFound(Exception):
    pass


class AbortConsume(Exception):
    pass


class DeadLetterMessage(Exception):
    pass
