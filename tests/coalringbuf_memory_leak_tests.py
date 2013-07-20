# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals, with_statement)

import gc
from threading import Lock

from nose.tools import eq_, ok_

from coalringbuf import CoalescingRingBuffer


class Counter(object):
    def __init__(self):
        self._lock = Lock()
        self._value = 0

    def increment(self):
        with self._lock:
            self._value += 1

    @property
    def value(self):
        return self._value


class CountingKey(object):
    def __init__(self, id, counter):
        self.id = id
        self.counter = counter

    def __eq__(self, other):
        return self is other or type(self) == type(other) and self.id == other.id

    def __del__(self):
        self.counter.increment()


class CountingValue(object):
    def __init__(self, counter):
        self.counter = counter

    def __del__(self):
        self.counter.increment()


def test_should_hot_have_memory_leaks():
    counter = Counter()
    buffer = CoalescingRingBuffer(16)

    buffer.offer(CountingValue(counter))

    for key in (1, 2, 1):
        buffer.offer(CountingKey(key, counter), CountingValue(counter))

    buffer.offer(CountingValue(counter))

    eq_(buffer.size, 4)

    buffer.poll([], 1)
    buffer.poll([])

    ok_(buffer.empty)

    # to trigger the clean
    buffer.offer(None)
    gc.collect()

    eq_(counter.value, 8)
