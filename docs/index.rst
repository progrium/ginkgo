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

.. autoclass:: ginkgo.core.Service
   
   .. attribute:: started
   
      This property returns whether this service has been started
   
   .. autoattribute:: ginkgo.core.Service.ready
   .. automethod:: ginkgo.core.Service._ready
   .. automethod:: ginkgo.core.Service.add_service
   .. automethod:: ginkgo.core.Service.remove_service
   .. automethod:: ginkgo.core.Service._start
   .. automethod:: ginkgo.core.Service._stop
   .. automethod:: ginkgo.core.Service.start
   .. automethod:: ginkgo.core.Service.stop
   .. automethod:: ginkgo.core.Service.serve_forever
   .. automethod:: ginkgo.core.Service.spawn
   .. automethod:: ginkgo.core.Service.spawn_later
   .. automethod:: ginkgo.core.Service.catch
   
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

