"""Utility module

Some useful gevent functions.

"""

import random

import gevent.socket

def line_protocol(socket_or_file, strip=True):
    """Generator for looping line-based protocol
    
    Takes a socket or file-from-socket and yields on every line. Disconnecting
    or connection errors will end the loop.
    
    """
    
    if hasattr(socket_or_file, 'makefile'):
        fileobj = socket_or_file.makefile()
    else:
        fileobj = socket_or_file
    while True:
        try:
            line = fileobj.readline() # returns None on EOF
            if line is not None and strip:
                line = line.strip()
        except IOError:
            line = None
        if line:
            yield line
        else:
            break

def connect_and_retry(address, source_address=None, max_retries=None, delay=1.0, max_delay=3600):
    """Connect and retry based on Twisted's ReconnectingClientFactory
    
    Wraps `gevent.socket.create_connection` with a loop for max_retries (if 
    given) using delay and max_delay (and several magic constants) to do a
    linear backoff with builtin jitter to avoid stampede.
    
    """
    factor = 2.7182818284590451 # (math.e)
    jitter = 0.11962656472 # molar Planck constant times c, joule meter/mole
    retries = 0
    
    while True:
        try:
            return gevent.socket.create_connection(address, source_address=source_address)
        except IOError:
            retries += 1
            if max_retries is not None and retries > max_retries:
                raise IOError("Unable to connect after %s retries" % max_retries)
            delay = min(delay * factor, max_delay)
            delay = random.normalvariate(delay, delay * jitter)
            gevent.sleep(delay)

class defaultproperty(object):
    """
    Allow for default-valued properties to be added to classes.

    Example usage:

    class Foo(object):
        bar = defaultproperty(list)
    """
    def __init__(self, default_factory, *args, **kwargs):
        self.default_factory = default_factory
        self.args = args
        self.kwargs = kwargs

    def __get__(self, instance, owner):
        if instance is None:
            return None
        for kls in owner.__mro__:
            for key, value in kls.__dict__.iteritems():
                if value == self:
                    newval = self.default_factory(*self.args, **self.kwargs)
                    instance.__dict__[key] =newval
                    return newval

