# Ginkgo

Lightweight service framework on top of gevent, implementing the "service model" -- services all the way down. 

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

## Authors

 * [Jeff Lindsay](jeff.lindsay@twilio.com)
 * [Sean McQuillan](sean@twilio.com)
 * [Alan Shreve](ashreve@twilio.com)
 * [Chad Selph](chad@twilio.com)
 * [Ryan Larrabure](ryan@twilio.com)

## License

MIT
