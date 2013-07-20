coalringbuf
===========

.. image:: https://travis-ci.org/jstasiak/coalringbuf.png?branch=master
   :alt: Build status
   :target: https://travis-ci.org/jstasiak/coalringbuf

*coalringbuf* is Python port of CoalescingRingBuffer from `LMAXCollections <https://github.com/LMAX-Exchange/LMAXCollections>`_. *coalringbuf* works with:

* CPython 2.x >= 2.5, 3.x >= 3.2
* PyPy 1.9+

Supported platforms: platform independent.

Status
------

It's usable and it passes port of original test suite.

Usage
-----

This port mimics original CoalescingRingBuffer API as closely as possible, however it was modified to make it more Pythonic.

Example intepreter session:

.. code-block:: python

    >>> from coalringbuf import CoalescingRingBuffer
    >>> buffer = CoalescingRingBuffer(3)
    >>> buffer.capacity
    4
    >>> buffer.empty
    True
    >>> buffer.offer('something')
    True
    >>> buffer.empty
    False
    >>> buffer.offer('something else')
    True
    >>> buffer.offer('quack')
    True
    >>> buffer.offer('id', 'value')
    True
    >>> buffer.size
    4
    >>> buffer.full
    True
    >>> buffer.offer('id', 'this will overwrite "value"')
    True
    >>> buffer.size
    4
    >>> buffer.offer('this will be rejected')
    False
    >>> buffer.size
    4
    >>> bucket = []
    >>> buffer.poll(bucket)
    4
    >>> bucket
    ['something', 'something else', 'quack', 'this will overwrite "value"']
    >>> buffer.empty
    True

TODO
----

* implement performance tests
* provide more efficient bucket class if needed


Copyright
---------

Original implementation (C) `LMAX <https://github.com/LMAX-Exchange>`_/`Nick Zeeb <https://github.com/nickzeeb>`_.

Python implementation (C) 2013 `Jakub Stasiak <https://github.com/jstasiak>`_.

This project is licensed under MIT license, see LICENSE file for details.
