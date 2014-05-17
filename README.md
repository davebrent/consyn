# Consyn

A [concatenative synthesis](http://en.wikipedia.org/wiki/Concatenative_synthesis)
command line tool.

## Dependencies

* [Python](https://python.org/)
* [Aubio](http://aubio.org/)
* [SQLite](https://sqlite.org/)

## Development

* Create a new virtualenv ``virtualenv env``
* Install python bindings for [aubio](https://github.com/piem/aubio/blob/master/python/README)
* Install the rest of the python dependencies ``pip install -r requirements.txt``
* ``python setup.py develop``
* ``python setup.py test``
