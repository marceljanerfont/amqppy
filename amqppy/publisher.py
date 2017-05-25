# -*- encoding: utf-8 -*-
import sys
import os
import pika
import uuid
import time
import logging
# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import amqppy
from amqppy import utils


logger = logging.getLogger(__name__)


def publish(broker, routing_key, body, headers=None, exchange=amqppy.AMQP_EXCHANGE, persistent=True):
    """Publish a message to the given exchange, routing key. This call creates a connection and once the message is sent the connection will be closed.
    Use class Publisher in case you want to reuse the same connection to send many messages.

    :param str broker: The URL for connection to RabbitMQ. Eg: 'amqp://serviceuser:password@rabbit.host:5672//'
    :param str rounting_key: The routing key to bind on
    :param str body: A json text is recommended. The body of the message you want to publish.
    :param dict headers: Message headers.
    :param str exchange: The exchange you want to publish the message.
    :param bool persistent: Makes message persistent. The message would not be lost after RabbitMQ restart.
    """
    publisher = Publisher(broker=broker)
    publisher.publish(exchange=exchange, routing_key=routing_key, body=body, persistent=persistent, headers=headers)


def rpc_request(broker, routing_key, body, exchange=amqppy.AMQP_EXCHANGE, timeout=10):
    """Makes a RPC request and returns its response. https://www.rabbitmq.com/tutorials/tutorial-six-python.html
    This call creates and destroys a connection every time, if you want to save connections, please use the class Rpc.

    :param str broker: The URL for connection to RabbitMQ. Eg: 'amqp://serviceuser:password@rabbit.host:5672//'
    :param str rounting_key: The routing key to bind on
    :param str body: A json text is recommended. The body of the request.
    :param str exchange: The exchange you want to publish the message.
    :param bool timeout: Maximum seconds to wait for the response.
    """
    rpc = Rpc(broker=broker)
    return rpc.request(exchange=exchange, routing_key=routing_key, body=body, timeout=timeout)

####################################################################


class Publisher(object):
    def __init__(self, broker):
        self._connection = utils._create_connection(broker=broker)

    def __del__(self):
        logger.debug("publisher destructor")
        if self._connection and self._connection.is_open:
            logger.debug("closeing connection")
            self._connection.close()

    def publish(self, exchange, routing_key, body, headers=None, persistent=True):
        """Publish a message to the given exchange, routing key.

        :param str exchange: The exchange you want to publish the message.
        :param str rounting_key: The rounting key to bind on
        :param str body: A json text is recommended. The Message you want to publish.
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
                                                       delivery_mode=2 if persistent else 1, headers=headers
                                                   ),  # 2 -> persistent
                                                   body=utils.json_dumps(body) if isinstance(body, dict) else body,
                                                   mandatory=True)  # to know if the message was routed
            if not publish_result:
                logger.debug("Publisher published message was not routed")
                raise amqppy.PublishNotRouted("Publisher published message was not routed")
        except pika.exceptions.ChannelClosed as e:
            if "NOT_FOUND - no exchange" in str(e):
                raise amqppy.ExchangeNotFound(str(e))

        finally:
            if channel and channel.is_open:
                logger.debug("closing channel")
                channel.close()


class Rpc(object):
    # def __init__(self, broker=None, host=None, port=5672, username="guest", password="guest", virtual_host="/"):
    #    self._connection = amqp_utils.__create_connection(broker=broker, host=host, port=port, username=username, password=password, virtual_host=virtual_host)

    def __init__(self, broker):
        self._connection = utils._create_connection(broker=broker)

    def __del__(self):
        logger.debug("rpc publisher destructor")
        if self._connection and self._connection.is_open:
            logger.debug("closeing connection")
            self._connection.close()

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            logger.debug("on_response: {}".format(body))
            self.response = body

    def request(self, exchange, routing_key, body, timeout):
        """Makes a RPC request and returns its response. https://www.rabbitmq.com/tutorials/tutorial-six-python.html
        This call creates and destroys a connection every time, if you want to save connections, please use the class Rpc.

        :param str rounting_key: The routing key to bind on
        :param str body: A json text is recommended. The body of the request.
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
            channel.basic_consume(queue=self.response_queue, consumer_callback=self.on_response, no_ack=True)

            logger.debug("publishing rpc request, exchange: {}, routing_key: {}, body: {}".format(self.exchange, routing_key, body))
            self.response = None
            self.corr_id = str(uuid.uuid4())
            publish_result = channel.basic_publish(exchange=self.exchange,
                                                   routing_key=routing_key,
                                                   properties=pika.BasicProperties(
                                                       reply_to=self.response_queue,
                                                       correlation_id=self.corr_id,
                                                       content_type='application/json',
                                                       delivery_mode=1),  # 2 -> persistent
                                                   body=body,
                                                   mandatory=True)
            if not publish_result:
                logger.debug("Rpc published message was not routed")
                raise amqppy.PublishNotRouted("Rpc published message was not routed")

            # wait for response
            logger.debug("waiting for rpc response... on \'{}\' for {} seconds".format(self.response_queue, timeout))
            start = time.time()
            while self.response is None:
                time.sleep(0.1)
                self._connection.process_data_events()
                if timeout > 0 and time.time() - start >= timeout:
                    logger.warning("AMQP RPC Timeout has been triggered waiting for the response")
                    raise amqppy.ResponseTimeout("AMQP RPC Timeout has been triggered waiting for the response")
            return self.response
        finally:
            if channel and channel.is_open:
                logger.debug("closing channel")
                channel.close()
