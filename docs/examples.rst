Usage Examples
==============
It required an accessible RabbitMQ and a Python environment with the **amqppy** package installed.

Topic Publisher-Subscribers
---------------------------
This is one of the most common messaging pattern where the publisher sends or publishes message to an AMQP exchange and the subscriber receives only the messages that are of interest. The subscribers' interest is modeled by the *Topic* or in terms of AMQP by the **rounting_key**. 

.. image:: https://www.rabbitmq.com/img/tutorials/python-five.png

Image from RabbitMQ `Topic tutorial <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_.
Firstly, we need to start the topic subscribers. In **amqppy** this task is done by the *amqppy.consumer.Worker* object.

Topic Subscriber
________________

.. code-block:: python

    from amqppy.consumer import Worker

    def on_topic_status(exchange, routing_key, headers, body):
        print('Received message from topic \'amqppy.publisher.topic.status\': {}'.format(body))

    # subscribe to a topic: 'amqppy.publisher.topic.status'
    worker = Worker(broker='amqp://guest:guest@localhost:5672//')
    worker.add_topic(exchange='amqppy.test',
                     routing_key='amqppy.publisher.topic.status',
                     on_topic_callback=on_topic_status)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()

The subscriber worker will invoke the *request_func* every time that the published message topic matches with the specified *routing_key*.

Once the topic subscriber is running we able to launch the publisher.

Topic Publisher
________________

.. code-block:: python

    from amqppy.publisher import Topic

    # publish my current status
    Topic(broker='amqp://guest:guest@localhost:5672//').publish(exchange='amqppy.test',
                                                                routing_key='amqppy.publisher.topic.status',
                                                                body='RUNNING')

The topic publisher will send a message to the AMQP exchange with the topic *'amqppy.publisher.topic.status'*, so then all the subscribed subscribers, *in case they do not share the same queue*, will receive the message.

RPC Request-Reply
-----------------
This pattern is commonly known as *Remote Procedure Call* or *RPC*. And is widely used when it's needed to run a function *request* on a remote computer and wait for the result *reply*.

.. image:: https://www.rabbitmq.com/img/tutorials/python-six.png

RPC reply
_________
It the *Worker* consumer that listens for incoming **requests** and computes the **reply** in the *on_request_callback*:

.. code-block:: python


Image from RabbitMQ `RPC tutorial <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_
