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
    """ Encapsulate the worker setup.

    Stablish a connection to the AMQP broker, and opens a channel for each consumer task.
    conn = Connection(host="localhost", userid="guest",password="guest", virtual_host="/")
    """
    def __init__(self, broker, heartbeat_sec=None):
        self._conn = utils._create_connection(broker=broker, heartbeat_sec=heartbeat_sec)
        # map(callback) -> (channel, exchange)
        self._callbacks = {}
        self.quit = False
        self.thread = None

    def __del__(self):
        logger.debug("consumer worker destructor")
        self._close()

    def _close(self):
        for callback in self._callbacks:
            if self._callbacks[callback].channel and self._callbacks[callback].channel.is_open:
                self._callbacks[callback].channel.close()
        self._callbacks = {}

        if self._conn:
            logger.debug('closing connection')
            self._conn.close()
            self._conn = None

    def _create_channel(self, exchange, request_func):
        try:
            channel = self._conn.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", passive=True)
            self._callbacks[request_func] = _ChannelExchange(channel, exchange)
            return channel
        except Exception:
            channel = self._conn.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", passive=False, durable=True, auto_delete=True)
            self._callbacks[request_func] = _ChannelExchange(channel, exchange)
            return channel

    def stop(self):
        logger.debug("stop")
        self.quit = True
        self.join()
        self._close()

    def add_request(self, routing_key, request_func, exchange=amqppy.AMQP_EXCHANGE, durable=False, auto_delete=True,
                    exclusive=False):
        """ Register a new consumer task. These tasks will be execute when a new message arrive
        at :param:`queue_name`, which is binded to the exchange with :param:`routing_key`.
        """
        logger.debug("adding request, exchange: {}, topic: {} --> {}".format(exchange, routing_key, request_func))
        channel = self._create_channel(exchange, request_func)
        channel.queue_declare(queue=routing_key, durable=durable, auto_delete=auto_delete)
        channel.queue_bind(queue=routing_key, exchange=exchange, routing_key=routing_key)
        channel.confirm_delivery()
        channel.basic_consume(
            exclusive=exclusive,
            queue=routing_key,
            consumer_callback=self._profiler_wrapper(request_func),
            no_ack=True)

        return self  # Fluent pattern

    def add_topic(self, routing_key, request_func, queue=None, exclusive=False, exchange=amqppy.AMQP_EXCHANGE, durable=False,
                  auto_delete=True, no_ack=True, **kwargs):
        """ Register a new consumer task. These tasks will be execute when a new message arrive
        at :param:`queue_name`, which is binded to the exchange with :param:`routing_key`.
        """
        logger.debug("adding topic, exchange: {}, topic: {} --> {}".format(exchange, routing_key, request_func, kwargs))
        self.no_ack = no_ack
        channel = self._create_channel(exchange, request_func)
        queue_name = queue if queue else routing_key
        channel.queue_declare(queue=queue_name, exclusive=exclusive, durable=durable, auto_delete=auto_delete,
                              arguments=kwargs)
        channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=routing_key)
        channel.basic_consume(
            queue=queue_name,
            consumer_callback=self._profiler_wrapper_topic(request_func),
            no_ack=no_ack)
        return self  # Fluent pattern

    def _profiler_wrapper(self, request_func):
        @wraps(request_func)
        def _wrapper(*args, **kwargs):
            logger.debug("request \'{}\'.*args: {}".format(request_func.__name__, args))
            # process request arguments
            deliver = args[1]
            properties = args[2]
            message = args[3]
            logger.debug("Starting request \'{}\'".format(request_func.__name__))
            # response = request_func(*args, **kwargs)
            start = time.time()
            try:
                response = {
                    # message is text, it should be converted in dictionary at request func
                    "result": request_func(exchange=deliver.exchange, routing_key=deliver.routing_key, headers=properties.headers, body=message),
                    "success": True
                }
            except Exception as e:
                logger.warning("Exception in request \'{}\', routing_key: {}\n{}".format(request_func.__name__,
                                                                                         deliver.routing_key,
                                                                                         traceback.format_exc()))
                response = {
                    "success": False,
                    "error": unicode(e)
                }
            elapsed = time.time() - start
            logger.debug('Request \'{}\' finished. Time elapsed: {}'.format(request_func.__name__, elapsed))

            # sending response back
            channel = self._callbacks[request_func].channel
            exchange = self._callbacks[request_func].exchange
            routing_key = properties.reply_to
            logger.debug('Sending RPC response to routing key: {}'.format(routing_key))
            try:
                publish_result = channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id,
                        content_type='application/json'),
                    body=json.dumps(response),
                    mandatory=True)
                if not publish_result:
                    raise amqppy.PublishNotRouted("Request response was not routed")
            except amqppy.PublishNotRouted:
                # don't raise it
                logger.warning("RPC response it has not been published, it might be due to a response waiting timeout")
            except Exception:
                logger.error('Exception on publish message to routing_key: {}. Exception message: {}'.format(
                    routing_key, traceback.format_exc()))
            logger.debug('RPC response sended.')
        return _wrapper

    def _profiler_wrapper_topic(self, request_func):
        @wraps(request_func)
        def _wrapper(*args, **kwargs):
            logger.debug("topic \'{}\'.*args: {}".format(request_func.__name__, args))
            # logger.debug("request \'{}\'.**kwargs: {}".format(request_func.__name__, kwargs))
            # process request arguments
            deliver = args[1]
            properties = args[2]
            message = args[3]
            # logger.debug("Properties vars: {}".format(vars(properties)))
            logger.debug("Starting request \'{}\'".format(request_func.__name__))
            start = time.time()
            try:
                request_func(exchange=deliver.exchange, routing_key=deliver.routing_key, headers=properties.headers, body=message)
                if not self.no_ack:
                    self._callbacks[request_func].channel.basic_ack(delivery_tag=deliver.delivery_tag)
                    logger.debug("ACK sent")
            except amqppy.AbortConsume as e:
                logger.warning("AbortConsume exception: {}".format(e))
            except amqppy.DeadLetterMessage as e:
                logger.warning("DeadLetterMessage exception: {}".format(e))
                self._callbacks[request_func].channel.basic_reject(delivery_tag=deliver.delivery_tag, requeue=False)
            finally:
                elapsed = time.time() - start
                logger.debug('Request \'{}\' finished. Time elapsed: {}'.format(request_func.__name__, elapsed))

        return _wrapper

    def run(self):
        """ Start consumption """
        logger.debug('Running worker, waiting for the first message...')
        while not self.quit:
            self._conn.process_data_events()
            time.sleep(0.1)
        logger.debug("Exiting worker.")

    def run_async(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        return self  # Fluent pattern

    def join(self):
        if self.thread:
            self.thread.join()
