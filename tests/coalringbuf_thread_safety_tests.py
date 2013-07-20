import os
from threading import Thread

from nose.tools import eq_
from six.moves import xrange

from coalringbuf import CoalescingRingBuffer

POISON_PILL = -1

FIRST_BID = 3
SECOND_BID = 4

FIRST_ASK = 5
SECOND_ASK = 6

NUMBER_OF_INSTRUMENTS = 1 * 10 ** 6 if 'COALRINGBUF_FULL_TEST' in os.environ else 5 * 10 ** 4


def test_should_see_last_prices():
    buffer = CoalescingRingBuffer(NUMBER_OF_INSTRUMENTS // 5)
    consumer_snapshots = [None] * NUMBER_OF_INSTRUMENTS
    producer_thread = Thread(target=producer, args=(buffer,))
    consumer_thread = Thread(target=consumer, args=(buffer, consumer_snapshots))

    producer_thread.start()
    consumer_thread.start()

    consumer_thread.join()

    for snapshot in consumer_snapshots:
        key, bid, ask = snapshot
        eq_((bid, ask), (SECOND_BID, SECOND_ASK), 'Bid/ask for instrument %r' % (key,))


def producer(buffer):
    def put(key, bid, ask):
        success = buffer.offer(key, (key, bid, ask))

        if not success:
            raise Exception('Adding key %r failed' % (key,))

    for key in xrange(NUMBER_OF_INSTRUMENTS):
        put(key, FIRST_BID, FIRST_ASK)
        put(key, SECOND_BID, SECOND_ASK)

    put(POISON_PILL, POISON_PILL, POISON_PILL)


def consumer(buffer, consumer_snapshots):
    use_limited_read = [False]

    def fill(bucket):
        buffer.poll(bucket, 1 if use_limited_read[0] else None)
        use_limited_read[0] = not use_limited_read[0]

    while True:
        bucket = []
        fill(bucket)

        for element in bucket:
            if element == (POISON_PILL, POISON_PILL, POISON_PILL):
                return
            else:
                key = element[0]
                consumer_snapshots[key] = element
