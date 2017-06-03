# -*- encoding: utf-8 -*-
import sys
import amqppy
import pika

if sys.version_info > (3,):
    import urllib.parse as urlparse  # pylint: disable=E0611,F0401
else:
    import urlparse


def create_url(host="localhost", port=5672, username="guest", password="guest", virtual_host="/", transport="amqp"):
    return "{}://{}:{}@{}:{}/{}".format(transport, username, password, host, port, virtual_host)


def parse_url(url):
    scheme = urlparse.urlparse(url).scheme
    schemeless = url[len(scheme) + 3:]
    # parse with HTTP URL semantics
    parts = urlparse.urlparse('http://' + schemeless)
    path = parts.path or ''
    path = path[1:] if path and path[0] == '/' else path
    return dict(
        transport=scheme,
        host=urlparse.unquote(parts.hostname or '') or None,
        port=parts.port or amqppy.DEFAULT_PORT,
        username=urlparse.unquote(parts.username or '') or None,
        password=urlparse.unquote(parts.password or '') or None,
        virtual_host=urlparse.unquote(path or '') or "/",
        **dict(urlparse.parse_qsl(parts.query)))


def _create_connection(broker, heartbeat_sec=None):
    # builds AMQP connection for each broker URL
    params = parse_url(broker)
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=params["host"],
        port=int(params["port"]),
        virtual_host=params["virtual_host"],
        credentials=pika.PlainCredentials(params["username"], params["password"]),
        socket_timeout=1.25,
        heartbeat_interval=heartbeat_sec))


def _ensure_utf8(body):
    if sys.version_info[0] < 3:
        # python 2
        return unicode(body).encode('utf8')
    else:
        # python 3
        return str(body).encode('utf8')


def _is_string(message):
    if sys.version_info[0] < 3:
        # python 2
        return isinstance(message, str) or isinstance(message, unicode)
    else:
        # python 3
        return isinstance(message, str)

