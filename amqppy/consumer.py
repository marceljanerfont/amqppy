# -*- encoding: utf-8 -*-
import traceback
from functools import wraps
import collections
# from collections import namedtupla
import pika
import logging
import threading
import time
import json
import sys
import os

# add amqppy path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import amqppy
from amqppy import utils


logger = logging.getLogger(__name__)

_ChannelExchange = collections.namedtuple('ChannelExchange', ['channel', 'exchange'])


class Worker(object):
    """ This class handles a worker that listens for incoming Topics and Rpc requests.

    :param str broker: The URL for connection to RabbitMQ. Eg: 'amqp://serviceuser:password@rabbit.host:5672//'
    """

    def __init__(self, broker, heartbeat_sec=None):
        # map(callback) -> (channel, exchange)
        self._callbacks = {}
        self.quit = False
        self.thread = None
        self._conn = None
        try:
            logger.debug("connecting to broker \'{}\'".format(broker))
            self._conn = utils._create_connection(broker=broker, heartbeat_sec=heartbeat_sec)
        finally:
            if self._conn and self._conn.is_open:
                logger.debug("connected")
            else:
                error = "Cannot connect to broker \'{}\'".format(broker)
                logger.error(error)
                raise amqppy.BrokenConnection(error)

    def __del__(self):
        # logger.debug("consumer worker destructor")
        self._close()

    def _close(self):
        for callback in self._callbacks:
            if self._callbacks[callback].channel and self._callbacks[callback].channel.is_open:
                self._callbacks[callback].channel.close()
        self._callbacks = {}
        if self._conn and self._conn.is_open:
            logger.debug('closing connection')
            self._conn.close()
            self._conn = None
            logger.debug('connection closed')

    def _create_channel(self, exchange, callback):
        try:
            channel = self._conn.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", passive=True)
            self._callbacks[callback] = _ChannelExchange(channel, exchange)
            return channel
        except Exception:
            channel = self._conn.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", passive=False, durable=True, auto_delete=True)
            self._callbacks[callback] = _ChannelExchange(channel, exchange)
            return channel

    def stop(self):
        """ Stops listening and close all channels and the connection
        """
        logger.debug("stop")
        self.quit = True
        self._join()
        self._close()

    def add_request(self, routing_key, on_request_callback, exchange=amqppy.AMQP_EXCHANGE, durable=False, auto_delete=True,
                    exclusive=False):
        """ Registers a new consumer for a RPC reply task. These tasks will be executed when a RPC request is invoked by
        publisher.Rpc.request().

        :param str rounting_key: It defines the subscription interest. In terms of AMQP the routing key to bind on
        :param method on_request_callback: Called when a Rpc request is invoked, it should return the reply.
        :param str exchange: The exchange you want to publish the message.
        :param bool durable: Queue messages survives a reboot of RabbitMQ.
        :param bool auto_delete: Queues will auto-delete after use.
        :param bool exclusive: Ensures that is the unique consumer
        """
        logger.debug("adding request, exchange: {}, topic: {} --> {}".format(exchange, routing_key, on_request_callback))
        channel = self._create_channel(exchange, on_request_callback)
        channel.queue_declare(queue=routing_key, durable=durable, auto_delete=auto_delete)
        channel.queue_bind(queue=routing_key, exchange=exchange, routing_key=routing_key)
        channel.confirm_delivery()
        try:
            channel.basic_consume(
                exclusive=exclusive,
                queue=routing_key,
                consumer_callback=self._profiler_wrapper_request(on_request_callback),
                no_ack=True)
        except pika.exceptions.ChannelClosed as e:
            if "in exclusive use" in str(e):
                raise amqppy.ExclusiveQueue(str(e))
            else:
                raise e

        return self  # Fluent pattern

    def _profiler_wrapper_request(self, on_request_callback):
        @wraps(on_request_callback)
        def _wrapper(*args, **kwargs):
            logger.debug("request \'{}\'.*args: {}".format(on_request_callback.__name__, args))
            # process request arguments
            deliver = args[1]
            properties = args[2]
            message = args[3]
            # convert message body to string
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            if not isinstance(message, str):
                logger.warning("_profiler_wrapper_request, type: {}, body: {}".format(type(message), message))

            logger.debug("Starting request \'{}\'".format(on_request_callback.__name__))
            # response = on_request_callback(*args, **kwargs)
            start = time.time()
            try:
                response = {
                    # message is text, it should be converted in dictionary at request func
                    "result": on_request_callback(exchange=deliver.exchange, routing_key=deliver.routing_key, headers=properties.headers, body=message),
                }
            except Exception as e:
                logger.warning("Exception in request \'{}\', routing_key: {}\n{}".format(on_request_callback.__name__,
                                                                                         deliver.routing_key,
                                                                                         traceback.format_exc()))
                response = {
                    "error": str(e, encoding='utf8')
                }
            elapsed = time.time() - start
            logger.debug('Request \'{}\' finished. Time elapsed: {}'.format(on_request_callback.__name__, elapsed))

            # sending response back
            channel = self._callbacks[on_request_callback].channel
            exchange = self._callbacks[on_request_callback].exchange
            routing_key = properties.reply_to
            logger.debug('Sending RPC response to routing key: {}'.format(routing_key))
            try:
                publish_result = channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id,
                        content_encoding='utf-8',
                        content_type='application/json'),
                    body=json.dumps(response, ensure_ascii=False).encode('utf8'),
                    mandatory=True)
                if not publish_result:
                    raise amqppy.PublishNotRouted("Request response was not routed")
            except amqppy.PublishNotRouted:
                # don't raise it
                logger.warning("RPC response it has not been published, it might be due to a response waiting timeout")
            except Exception:
                logger.error('Exception on publish message to routing_key: {}. Exception message: {}'.format(
                    routing_key, traceback.format_exc()))
            logger.debug('RPC response sent.')
        return _wrapper

    def add_topic(self, routing_key, on_topic_callback, queue=None, exclusive=False, exchange=amqppy.AMQP_EXCHANGE, durable=False,
                  auto_delete=True, no_ack=True, **kwargs):
        """ Registers a new consumer for a Topic subscriber. These tasks will be executed when a Topic is published by
        publisher.Topic.publish().

        :param str rounting_key: The routing key to bind on.
        :param method on_topic_callback: Called when a topic is published.
        :param str queue: The name of the queue. If it is not provided the queue will be named the same as the 'routing_key'.
        :param bool exclusive: Only one consumer is allowed.
        :param str exchange: The exchange you want to publish the message.
        :param bool durable: Queue messages survives a reboot of RabbitMQ.
        :param bool auto_delete: Queues will auto-delete after use.
        :param bool no_ack: Tell the broker that ACK reply is not needed. If it is False, an ACK will be sent automatically each \
        time a message is consumed unless a amqppy.AbortConsume or amqppy.DeadLetterMessage is raised.
        """
        logger.debug("adding topic, exchange: {}, topic: {} --> {}".format(exchange, routing_key, on_topic_callback, kwargs))
        self.no_ack = no_ack
        channel = self._create_channel(exchange, on_topic_callback)
        queue_name = queue if queue else routing_key
        channel.queue_declare(queue=queue_name, durable=durable, auto_delete=auto_delete,
                              arguments=kwargs)
        channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=routing_key)
        try:
            channel.basic_consume(
                queue=queue_name,
                exclusive=exclusive,
                consumer_callback=self._profiler_wrapper_topic(on_topic_callback),
                no_ack=no_ack)
        except pika.exceptions.ChannelClosed as e:
            if "in exclusive use" in str(e):
                raise amqppy.ExclusiveQueue(str(e))
            else:
                raise e
        return self  # Fluent pattern

    def _profiler_wrapper_topic(self, on_topic_callback):
        @wraps(on_topic_callback)
        def _wrapper(*args, **kwargs):
            logger.debug("topic \'{}\'.*args: {}".format(on_topic_callback.__name__, args))
            # logger.debug("request \'{}\'.**kwargs: {}".format(on_topic_callback.__name__, kwargs))
            # process request arguments
            deliver = args[1]
            properties = args[2]
            message = args[3]
            # convert message body to string
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            if not utils._is_string(message):
                logger.warning("_profiler_wrapper_topic, message in not string, is of type: {}".format(type(message)))
            # logger.debug("Properties vars: {}".format(vars(properties)))
            logger.debug("Starting request \'{}\'".format(on_topic_callback.__name__))
            start = time.time()
            try:
                on_topic_callback(exchange=deliver.exchange, routing_key=deliver.routing_key, headers=properties.headers, body=message)
                if not self.no_ack:
                    self._callbacks[on_topic_callback].channel.basic_ack(delivery_tag=deliver.delivery_tag)
                    logger.debug("ACK sent")
            except amqppy.AbortConsume as e:
                logger.warning("AbortConsume exception: {}".format(e))
            except amqppy.DeadLetterMessage as e:
                logger.warning("DeadLetterMessage exception: {}".format(e))
                self._callbacks[on_topic_callback].channel.basic_reject(delivery_tag=deliver.delivery_tag, requeue=False)
            finally:
                elapsed = time.time() - start
                logger.debug('Request \'{}\' finished. Time elapsed: {}'.format(on_topic_callback.__name__, elapsed))

        return _wrapper

    def run(self):
        """ Start worker to listen. This will block the execution until the worker is stopped or an uncaught Exception  """
        logger.info('Running worker, waiting for the first message...')
        try:
            while not self.quit:
                self._conn.process_data_events(0.5)
        finally:
            logger.info("exiting from worker run")

    def run_async(self):
        """ Start asynchronously worker to listen. The execution thread will follow after this call, hence is not blocked.  """
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        return self  # Fluent pattern

    def _join(self):
        """ Waits until worker has ended """
        if self.thread and self.thread.is_alive():
            self.thread.join()
