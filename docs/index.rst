Introduction to amqppy
======================
amqppy is a very simplified AMQP client stacked over Pika. It has been tested with RabbitMQ, but it should also work with other AMQP 0-9-1 brokers.


Installing amqppy
-----------------
Pika is available for download via PyPI and may be installed using easy_install or pip::

    pip install amqppy

or::

    easy_install amqppy

To install from source, run "python setup.py install" in the root source directory.


Usage Examples
==============

Topic publisher subscriber
--------------------------
Fristly run *examples/topic_consumer.py*

        examples/topic_publisher.py
        examples/topic_consumer.py