Introduction
============

Origin
------
Ginkgo evolved from a project called "gevent_tools" that started as a
collection of common features needed when building gevent applications. The
author had previously made a habit of building lots of interesting little
servers as a hobby, and then at work found himself writing and dealing with
lots more given the company's service oriented architecture. Accustomed to using
the application framework in Twisted, when he finally saw the light and
discovered gevent, there was no such framework for that paradigm.

Dealing with so many projects, it was not practical to reinvent the same basic
features and architecture over and over again. The same way web frameworks made
it easy to "throw together" a web application, there needed to be a way to
quickly "throw together" network daemons. Not just simple one-off servers, but
large-scale, complex applications -- often part of a larger distributed system.

Through the experience of building large systems, a pattern emerged that was
like a looser, more object-oriented version of the actor model based around the
idea of services. This became the main feature of gevent_tools and it was later
renamed gservice. However, with the hope of supporting other async mechanisms
other than gevent's green threads (such as actual threads or processes, or
other similar network libraries), the project was renamed Ginkgo.

Vision
------
The Ginkgo microframework is a minimalist foundation for building very large
systems, beyond individual daemons. There were originally plans for
gevent_tools to include higher-level modules to aid in developing distributed
applications, such as service discovery and messaging primitives.

While Ginkgo will remain focused on "baseline" features common to pretty much
all network daemons, a supplementary project to act as a "standard library" for
Ginkgo applications is planned. Together with Ginkgo, the vision would be to
quickly "throw together" distributed systems from simple primitives.

Inspiration
-----------
Most of Ginkgo was envisioned by taking good ideas from other projects,
simplifying to their essential properties, and integrating them together. A lot
of thanks goes out to these projects.

Twisted is the first great Python evented daemon framework. The two big ideas
borrowed from Twisted are their application framework and twistd. They directly
inspired the service model and the Ginkgo runner.

Trac is known for the problem it solves, and not so much for its great
architecture. However, its component model and configuration API were a big
influence on Ginkgo. Trac components are how we think of Ginkgo services, and
the way Ginkgo defines configuration settings is directly inspired by the Trac
configuration API.

These projects also had some influence on Ginkgo's design and philosophy:
Gunicorn, Mongrel, Apache, Django, Flask, python-daemon, Diesel, Tornado,
Erlang/OTP, Typeface, Akka, Configgy, Ostrich, and others.
