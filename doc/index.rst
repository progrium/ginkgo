.. gevent-tools documentation master file, created by
   sphinx-quickstart on Sun May  8 03:34:49 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

gevent-tools is a collection of mini-libraries and utilities built on gevent for building gevent applications. There are currently three modules:

- :mod:`service` Provides a base class for implementing services, which are a nice way to organize large gevent applications. Services contain greenlets and other services, and provide a good foundation to build the components of any application.
- :mod:`cluster` A distributed roster manager for clusters for building distributed apps that need to know other hosts available in the cluster.
- :mod:`util` A couple of utility methods for building network applications in gevent

Building services
=================

.. autoclass:: gevent_tools.service.Service
   
   .. attribute:: started
   
      This property returns whether this service has been started
   
   .. autoattribute:: gevent_tools.service.Service.ready
   .. automethod:: gevent_tools.service.Service._ready
   .. automethod:: gevent_tools.service.Service.add_service
   .. automethod:: gevent_tools.service.Service.remove_service
   .. automethod:: gevent_tools.service.Service._start
   .. automethod:: gevent_tools.service.Service._stop
   .. automethod:: gevent_tools.service.Service.start
   .. automethod:: gevent_tools.service.Service.stop
   .. automethod:: gevent_tools.service.Service.serve_forever
   .. automethod:: gevent_tools.service.Service.spawn
   .. automethod:: gevent_tools.service.Service.spawn_later
   .. automethod:: gevent_tools.service.Service.catch
   
Utilities
=========

.. automodule:: gevent_tools.util
   :members:

Contents:

.. toctree::
   :maxdepth: 2
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

