# Ginkgo

Lightweight service framework on top of gevent, implementing the "service model" -- services all the way down.

## Features
* Service model -- Break your app down into services and sub-services.
  Modules, if you will, that can start, stop, and reload. Every service
  manages its own pool of greenlets.
* Configuration -- Built-in, reloadable configuration based on Python
  files. Access configuration settings relative to services.
* Runner -- Command-line tool to manage your service that can daemonize,
  chroot, drop privs, and set up or override configuration.

## Mailing List

Pretty active discussion on this early microframework. Join it or just
read what's being planned:
* [Ginkgo-dev Google Group](http://groups.google.com/group/ginkgo-dev)

## Contributing

Feel free to poke around the issues in the main repository and see if you can tackle any. From there you should:

* Fork if you haven't
* Create a branch for the feature / issue
* Write code+tests
* Pass tests (using nose)
* Squash branch commits using [merge and reset](http://j.mp/vHLUoa)
* Send pull request

We highly recommend using branches for all features / issues and then squashing it into a single commit in your master before issuing a pull request. It's actually quite easy using [merge and reset](http://j.mp/vHLUoa). This helps keep features and issues consolidated, but also makes pull requests easier to read, which increases the speed and likelihood of being accepted.

We're aiming for at least 90% test coverage. If you have the `coverage` Python package installed, you can run `python setup.py coverage` to get a coverage report of modules within gservice.

## Contributors

 * [Jeff Lindsay](jeff.lindsay@twilio.com)
 * [Sean McQuillan](sean@twilio.com)
 * [Alan Shreve](ashreve@twilio.com)
 * [Chad Selph](chad@twilio.com)
 * [Ryan Larrabure](ryan@twilio.com)

## License

MIT
