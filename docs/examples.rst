Usage Examples
==============
It requires an accessible RabbitMQ and a Python environment with the **amqppy** package installed.

Topic Publisher-Subscribers
---------------------------
This is one of the most common messaging pattern where the publisher publishes message to an AMQP exchange and the subscriber receives only the messages that are of interest. The subscriber's interest is modeled by the *Topic* or in terms of AMQP by the **rounting_key**. 

.. image:: https://www.rabbitmq.com/img/tutorials/python-five.png

Image from RabbitMQ `Topic tutorial <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_.

Topic Subscriber
________________
Firstly, we need to start the Topic Subscriber (*also known as Consumer*). In **amqppy** the class **amqppy.consumer.Worker** has this duty.

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

The subscriber worker will invoke the *on_topic_callback* every time a message is published with a topic that matches with the specified **routing_key**: `'amqppy.publisher.topic.status'`. Note that **routing_key** can contain `wildcards <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_ therefore, one subscriber might be listening a set of *Topics*.

Once the topic subscriber is running we able to launch the publisher.

Topic Publisher
________________

.. code-block:: python

    from amqppy.publisher import Topic

    # publish my current status
    Topic(broker='amqp://guest:guest@localhost:5672//').publish(exchange='amqppy.test',
                                                                routing_key='amqppy.publisher.topic.status',
                                                                body='RUNNING')

The topic publisher will send a message to the AMQP exchange with the Topic **routing_key**: `'amqppy.publisher.topic.status'`, therefore, all the subscribed subscribers will receive the message unless they do not share the same queue. In case they share the same queue a round-robin dispatching policy would be applied among subscribers/consumers like happens in `work queues <https://www.rabbitmq.com/tutorials/tutorial-two-python.html>`_*.

RPC Request-Reply
-----------------
This pattern is commonly known as *Remote Procedure Call* or *RPC*. And is widely used when we need to run a function *request* on a remote computer and wait for the result *reply*.

.. image:: https://www.rabbitmq.com/img/tutorials/python-six.png

Image from RabbitMQ `RPC tutorial <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_

RPC Reply
_________
An object of type **amqppy.consumer.Worker** listens incoming **RPC requests** and computes the **RPC reply** in the *on_request_callback*. In the example below, the RPC consumer listens on Request **rounting_key**:`'amqppy.requester.rpc.division'` and the division would be returned as the RPC reply.

.. code-block:: python

    from amqppy.consumer import Worker

    def on_rpc_request_division(exchange, routing_key, headers, body):
        args = json.loads(body)
        return args['dividend'] / args['divisor']

    # subscribe to a rpc request: 'amqppy.requester.rpc.division'
    worker = Worker(broker='amqp://guest:guest@localhost:5672//')
    worker.add_request(exchange='amqppy.test',
                       routing_key='amqppy.requester.rpc.division',
                       on_request_callback=on_rpc_request_division)
    # it will wait until worker is stopped or an uncaught exception
    worker.run()


RPC Request
___________
The code below shows how to do a **RPC Request** using an instance of class *amqppy.publisher.Rpc*

.. code-block:: python

    from amqppy.publisher import Rpc

    # do a Rpc request 'amqppy.requester.rpc.division'
    result = Rpc(broker='amqp://guest:guest@localhost:5672//').request(exchange='amqppy.test',
                                             routing_key='amqppy.requester.rpc.division',
                                             body=json.dumps({'dividend': 3.23606797749979, 'divisor': 2.0}))
    print('RPC result: {}.'.format(result))
