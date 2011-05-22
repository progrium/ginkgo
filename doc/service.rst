Service component
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