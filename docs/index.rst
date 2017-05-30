Introduction to amqppy
======================
**amqppy** is a very simplified AMQP client stacked over `Pika <https://github.com/pika/pika>`_. It has been tested with `RabbitMQ <https://www.rabbitmq.com>`_, however it should also work with other AMQP 0-9-1 brokers.

The motivation of **amqppy** is to provide a very simplified and minimal AMQP client interface which can help Python developers to implement easily messaging patterns such as:

* `Topic Publisher-Subscribers <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_
* `RPC Request-Reply <https://www.rabbitmq.com/tutorials/tutorial-six-python.html>`_

Others derivative `messaging patterns <https://www.rabbitmq.com/getstarted.html>`_ can be implemented tunning some parameters of the Topic and Rpc objects.

Installing amqppy
-----------------
**amqppy** is available for download via PyPI and may be installed using easy_install or pip::

    pip install amqppy


To install from source, run "python setup.py install" in the root source directory.

Home of amqppy
--------------
`https://github.com/marceljanerfont/amqppy <https://github.com/marceljanerfont/amqppy>`_

Using amqppy
============
.. toctree::
   :glob:
   :maxdepth: 1

   examples
   modules/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`