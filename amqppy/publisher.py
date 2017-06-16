# -*- encoding: utf-8 -*-
import sys
import os
import pika
import uuid
import json
import logging
# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import amqppy
from amqppy import utils


logger = logging.getLogger(__name__)


class Topic(object):
    """This class creates a connection to the message broker and provides a method to publish messages on
    one topic also known as routing_key in AMQP terms. The class instance will create on single connection
    to the broker for all the topic published.

    :param str broker: The URL for connection to RabbitMQ. Eg: 'amqp://serviceuser:password@rabbit.host:5672//'
    """

    def __init__(self, broker):
        self._connection = None
        try:
            logger.debug("connecting to broker \'{}\'".format(broker))
            self._connection = utils._create_connection(broker=broker)
        finally:
            if self._connection and self._connection.is_open:
                logger.debug("connected")
            else:
                error = "Cannot connect to broker \'{}\'".format(broker)
                logger.error(error)
                raise amqppy.BrokenConnection(error)

    def __del__(self):
        logger.debug("publisher destructor")
        if self._connection and self._connection.is_open:
            logger.debug("closeing connection")
            self._connection.close()

    def publish(self, exchange, routing_key, body, headers=None, persistent=True):
        """Publish a message to the given exchange and a routing key.

        :param str exchange: The exchange you want to publish the message.
        :param str rounting_key: The rounting key to bind on
        :param str body: The body of the message you want to publish. It should be of type unicode or string encoded with UTF-8.
        :param dict headers: Message headers.
        :param bool persistent: Makes message persistent. The message would not be lost after RabbitMQ restart.
        """
        logger.debug("creating channel")
        channel = self._connection.channel()
        try:
            channel.confirm_delivery()
            logger.debug("publishing message at exchange: {} and routing_key: {}".format(exchange, routing_key))
            publish_result = channel.basic_publish(exchange=exchange,
                                                   routing_key=routing_key,
                                                   properties=pika.BasicProperties(
                                                       content_encoding='utf-8',
                                                       delivery_mode=2 if persistent else 1, headers=headers,  # 2 -> persistent
                                                   ),
                                                   body=utils._ensure_utf8(body),
                                                   mandatory=True)  # to know if the message was routed
            if not publish_result:
                logger.debug("Publisher published message was not routed")
                raise amqppy.PublishNotRouted("Publisher published message was not routed")
        except pika.exceptions.ChannelClosed as e:
            if "NOT_FOUND - no exchange" in str(e):
                raise amqppy.ExchangeNotFound(str(e))
            else:
                raise e

        finally:
            if channel and channel.is_open:
                logger.debug("closing channel")
                channel.close()


class Rpc(object):
    """The duty of Rpc class is to make RPC requests and returns its responses.
    `RPC pattern tutorial <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_.
    The class instance will create on single connection to the broker for all the RPC requests.

    :param str broker: The URL for connection to RabbitMQ. Eg: 'amqp://serviceuser:password@rabbit.host:5672//'
    """

    def __init__(self, broker):
        self._connection = None
        try:
            logger.debug("connecting to broker \'{}\'".format(broker))
            self._connection = utils._create_connection(broker=broker)
        finally:
            if self._connection and self._connection.is_open:
                logger.debug("connected")
            else:
                error = "Cannot connect to broker \'{}\'".format(broker)
                logger.error(error)
                raise amqppy.BrokenConnection(error)

    def __del__(self):
        logger.debug("rpc destructor")
        if self._connection and self._connection.is_open:
            # logger.debug("closeing connection")
            self._connection.close()

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if not isinstance(body, str):
                logger.warning("_on_response, type: {}, body: {}".format(type(body), body))
            logger.debug("_on_response body: {}".format(body))
            self.response = json.loads(body)

    def request(self, exchange, routing_key, body, timeout=10.0):
        """Makes a RPC request and returns its response.
        `RPC pattern tutorial <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_.
        This call creates and destroys a connection every time, if you want to save connections, please use the class Rpc.

        :param str rounting_key: The routing key to bind on
        :param str body: The body of the message request you want to request. It should be of type unicode or string encoded with UTF-8.
        :param str exchange: The exchange you want to publish the message.
        :param bool timeout: Maximum seconds to wait for the response.
        """
        self.exchange = exchange
        channel = self._connection.channel()
        # Enabled delivery confirmations:
        # very important to know if the message was delivered or consumed
        channel.confirm_delivery()

        try:
            # rpc response queue
            self.response_queue = channel.queue_declare(exclusive=True).method.queue
            channel.queue_bind(queue=self.response_queue, exchange=self.exchange, routing_key=self.response_queue)

            # lets listen response
            channel.basic_consume(queue=self.response_queue, consumer_callback=self._on_response, no_ack=True)

            logger.debug("publishing rpc request, exchange: {}, routing_key: {}, body: {}".format(self.exchange, routing_key, body))
            self.response = None
            self.corr_id = str(uuid.uuid4())
            publish_result = channel.basic_publish(exchange=self.exchange,
                                                   routing_key=routing_key,
                                                   properties=pika.BasicProperties(
                                                       reply_to=self.response_queue,
                                                       correlation_id=self.corr_id,
                                                       content_encoding='utf-8',
                                                       delivery_mode=1),  # 2 -> persistent
                                                   body=utils._ensure_utf8(body),
                                                   mandatory=True)
            if not publish_result:
                logger.debug("Rpc published message was not routed")
                raise amqppy.PublishNotRouted("Rpc published message was not routed")

            # wait for response
            timeout = max(timeout, 0.1)
            logger.debug("waiting for rpc response... on \'{}\' for {} seconds".format(self.response_queue, timeout))
            self._connection.process_data_events(timeout)
            if not self.response:
                logger.warning("Rpc Timeout has been triggered waiting for the response")
                raise amqppy.ResponseTimeout("Rpc Timeout has been triggered waiting for the response")
            """
            start = time.time()
            while self.response is None:
                self._connection.process_data_events(min(timeout, 1.0))
                if timeout > 0 and time.time() - start >= timeout:
                    logger.warning("AMQP RPC Timeout has been triggered waiting for the response")
                    raise amqppy.ResponseTimeout("AMQP RPC Timeout has been triggered waiting for the response")
            """
            # we have the rpc reply
            # is success?
            if "result" in self.response:
                return self.response["result"]
            else:
                str_error = "Unknown RPC error"
                if "error" in self.response:
                    str_error = self.response["error"]
                raise amqppy.RpcRemoteException(str_error)
        except pika.exceptions.ChannelClosed as e:
            if "NOT_FOUND - no exchange" in str(e):
                raise amqppy.ExchangeNotFound(str(e))
            else:
                raise e
        finally:
            if channel and channel.is_open:
                logger.debug("closing channel")
                channel.close()
