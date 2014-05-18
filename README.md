# Consyn

A [concatenative synthesis](http://en.wikipedia.org/wiki/Concatenative_synthesis)
command line tool.

Consyn takes audio files and slices them into short sections of sound, called
units. Units are analysed and their audible characteristics, called features,
are stored. Units can then be selected with different algorithms, based on their
features, and concatenated together to create entirely new sounds.

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
