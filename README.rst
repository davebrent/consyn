Consyn
======

.. image:: https://travis-ci.org/davebrent/consyn.svg?branch=master
    :target: https://travis-ci.org/davebrent/consyn

.. image:: https://coveralls.io/repos/davebrent/consyn/badge.png?branch=master
    :target: https://coveralls.io/r/davebrent/consyn?branch=master

A `concatenative synthesis`_ command line tool.

.. _concatenative synthesis: http://en.wikipedia.org/wiki/Concatenative_synthesis

Dependencies
------------

- `Python`_
- `SQLite`_
- `Aubio`_ (optional)

.. _Python: https://python.org/
.. _SQLite: https://sqlite.org/
.. _Aubio: http://aubio.org/

Development
-----------
 ::

    virtualenv env
    pip install -r requirements.txt
    python setup.py develop
    nosetests
