# Consyn (Work in progress)

A [Concatenative synthesis](http://en.wikipedia.org/wiki/Concatenative_synthesis)
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

## Usage

Calculate audio features and add files to a local sqlite database

    consyn add path/to/some/audio.mp3
    consyn add path/to/more/audio.wav
    consyn add path/to/another.mp3

Print the current contents of the database

    consyn status

Create and save an audio mosaic to ``outputfile.wav``, using the first file
added, as the target and the second and third files added as sources for
fragments of sound.

    consyn mosaic outputfile.wav 1 2 3
