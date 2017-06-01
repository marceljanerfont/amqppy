from setuptools import setup
import amqppy

long_description = ('amqppy is a very simplified AMQP client stacked over Pika. '
                    'amqppy is tested with RabbitMQ, but should also work '
                    'with other AMQP 0-9-1 brokers.')

setup(name='amqppy',
      version=amqppy.__version__,
      description='amqppy is a very simplified AMQP client stacked over Pika',
      keywords=['amqp', 'client', 'rabbitmq', 'amqp client'],
      long_description=open('README.rst').read(),
      author='Marcel Janer Font',
      author_email='marceljanerfont@gmail.com',
      maintainer='Marcel Janer Font',
      maintainer_email='marceljanerfont@gmail.com',
      url='https://github.com/marceljanerfont/amqppy',
      packages=['amqppy'],
      license='MIT',
      install_requires=['pika'],
      package_data={'': ['LICENSE', 'README.rst']},
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: Jython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Communications',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Networking'],
      zip_safe=True)
