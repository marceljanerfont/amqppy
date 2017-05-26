Introduction to amqppy
======================
amqppy is a very simplified AMQP client stacked over Pika. It has been tested with RabbitMQ, but it should also work with other AMQP 0-9-1 brokers.


Installing amqppy
-----------------
Pika is available for download via PyPI and may be installed using easy_install or pip::

    pip install amqppy


To install from source, run "python setup.py install" in the root source directory.


Usage Examples
==============
It required an accessible RabbitMQ and a Python environment with the **amqppy** package installed.

Topic publisher-subscriber
--------------------------
This is one of the most common messaging pattern where the publisher sends or publishes message to an AMQP exchange and the subscriber receives only the messages that are of interest. The subscribers interest is modeled by the *Topic* or in terms of AMQP by the **rounting_key**.

First we need to start the subscriber. In **amqppy** this task is done by the *amqppy.consumer.Worker* object:

.. code-block:: python

    from amqppy import consumer

    def on_topic_status(exchange, routing_key, headers, body):
        print('Received message from topic \'amqppy.publisher.topic.status\': {}'.format(body))

    # subscribe to a topic: 'amqppy.publisher.topic.status'
    worker = consumer.Worker(broker='amqp://guest:guest@localhost:5672//')
    worker.add_topic(exchange='amqppy.test',
                     routing_key='amqppy.publisher.topic.status',
                     request_func=on_topic_status)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()

The subscriber worker will invoke the *request_func* every time that the published message topic matches with the specified *routing_key*.

One the topic consumer (*subscriber*) is running we can launch the publisher:

.. code-block:: python

    from amqppy import publisher

    # publish my current status
    publisher.publish(broker='amqp://guest:guest@localhost:5672//',
                      exchange='amqppy.test',
                      routing_key='amqppy.publisher.topic.status',
                      body='RUNNING')

And the topic publisher will send a message to the AMQP exchange with the topic *'amqppy.publisher.topic.status'*, so then all the subscribers, in case they do not share the same queue, will receive the message.


