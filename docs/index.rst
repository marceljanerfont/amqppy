Introduction to amqppy
======================
**amqppy** is a very simplified AMQP client stacked over `Pika <https://github.com/pika/pika>`_. It has been tested with `RabbitMQ <https://www.rabbitmq.com>`_, however it should also work with other AMQP 0-9-1 brokers.

The motivation of **amqppy** is to provide a very simplified and minimal AMQP client interface which can help Python developers to implement easily messaging patterns such as:

* `Topic Publisher-Subscribers <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_
* `RPC Request-Reply <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_

And other derivative `messaging patterns <https://www.rabbitmq.com/getstarted.html>`_.


Installing amqppy
-----------------
Pika is available for download via PyPI and may be installed using easy_install or pip::

    pip install amqppy


To install from source, run "python setup.py install" in the root source directory.


Usage Examples
==============
It required an accessible RabbitMQ and a Python environment with the **amqppy** package installed.

TTopic Publisher-Subscribers
--------------------------
This is one of the most common messaging pattern where the publisher sends or publishes message to an AMQP exchange and the subscriber receives only the messages that are of interest. The subscribers' interest is modeled by the *Topic* or in terms of AMQP by the **rounting_key**. 

.. image:: https://www.rabbitmq.com/img/tutorials/python-five.png
Image from RabbitMQ `Topic tutorial <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_.

Firstly, we need to start the topic subscribers. In **amqppy** this task is done by the *amqppy.consumer.Worker* object.

Topic Subscriber
________________

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

Once the topic ubscriber is running we able to launch the publisher.

Topic Publisher
________________

.. code-block:: python

    from amqppy import publisher

    # publish my current status
    publisher.publish(broker='amqp://guest:guest@localhost:5672//',
                      exchange='amqppy.test',
                      routing_key='amqppy.publisher.topic.status',
                      body='RUNNING')

The topic publisher will send a message to the AMQP exchange with the topic *'amqppy.publisher.topic.status'*, so then all the subscribed subscribers, *in case they do not share the same queue*, will receive the message.

RPC Request-Reply
-----------------

.. image:: https://www.rabbitmq.com/img/tutorials/python-six.png
Image from RabbitMQ `RPC tutorial <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_.
