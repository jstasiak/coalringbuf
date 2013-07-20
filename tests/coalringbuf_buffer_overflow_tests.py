# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
from threading import Thread

from nose.tools import ok_
from six.moves import xrange

from coalringbuf import CoalescingRingBuffer


POISON_PILL = -1
ITERATIONS = 10 ** 6 if 'COALRINGBUF_FULL_TEST' in os.environ else 10 ** 5


def test_should_be_able_to_reuse_capacity():
    buffer = CoalescingRingBuffer(32)
    has_overflowed = [False]
    producer_thread = Thread(target=producer, args=(buffer, has_overflowed))
    consumer_thread = Thread(target=consumer, args=(buffer,))

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    ok_(not has_overflowed[0])


def producer(buffer, has_overflowed):
    for run in xrange(ITERATIONS):
        for message in range(10):
            success = buffer.offer(message, message)

            if not success:
                has_overflowed[0] = True
                buffer.offer(POISON_PILL)
                return

    buffer.offer(POISON_PILL)


def consumer(buffer):
    running = True
    while running:
        bucket = []
        buffer.poll(bucket, 100)
        running = POISON_PILL not in bucket
