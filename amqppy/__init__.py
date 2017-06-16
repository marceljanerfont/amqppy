# -*- encoding: utf-8 -*-
__version__ = '0.0.18'

DEFAULT_PORT = 5672
AMQP_EXCHANGE = "amqppy"
AMQP_BROKER = "amqp://localhost:{}//".format(DEFAULT_PORT)

from .utils import create_url, parse_url
from .consumer import Worker
from .publisher import Topic, Rpc

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


class BrokenConnection(Exception):
    '''
    It would be raised when the connection to the broker fails
    '''
    pass


class RpcRemoteException(Exception):
    '''
    It would be raised in the publisher.Rpc.request() when remote reply fails
    '''
    pass


class ResponseTimeout(Exception):
    '''
    It would be raised in the publisher.Rpc.request() when remote reply exceeds its allowed execution time, the timeout.
    '''
    pass


class PublishNotRouted(Exception):
    '''
    It would be raised in the publisher.Rpc.request() or publisher.Topic.publish() when there is no consumer listening
    those Topics or Rpc requests.
    '''
    pass


class ExclusiveQueue(Exception):
    '''
    It would be raised in the consumer.Worker.add_topic() or consumer.Worker.add_request() when tries to consume from a queue
    where there is already a consumer listening. That happens when add_topic or add_request is called with 'exclusive=True'.
    '''
    pass


class ExchangeNotFound(Exception):
    '''
    It will be raised when AMQP Exchange does not exist.
    '''
    pass


class AbortConsume(Exception):
    '''
    This exception can be raised by the Topic callback or RPC reply callback. And indicates to amqppy to do not send ACK
    for that consuming message. For this, is required 'no_ack=False' in consumer.Worker.add_topic() or consumer.Worker.add_request()
    '''
    pass


class DeadLetterMessage(Exception):
    '''
    This exception can be raised by the Topic callback or RPC reply callback. And indicates to amqppy to move this
    message is being consumed to the DeadLetter Queue. See: 'https://www.rabbitmq.com/dlx.html'
    '''
    pass
