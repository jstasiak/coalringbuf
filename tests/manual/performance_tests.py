from __future__ import absolute_import, division, print_function, unicode_literals

import gc
from threading import Event, Thread
from time import sleep, time

from coalringbuf import CoalescingRingBuffer


NANO = 1.0 / 10 ** 9


class StopWatch(object):
    def __init__(self):
        self._producer_started = Event()
        self._consumer_started = Event()
        self._start_time = None

    def producer_started(self):
        self._producer_started.set()
        self._consumer_started.wait()

    def consumer_started(self):
        self._consumer_started.set()
        self._producer_started.wait()
        self._start_time = time()

    def consumer_stopped(self):
        self._nanos_taken = (time() - self._start_time) / NANO

    @property
    def nanos_taken(self):
        return self._nanos_taken


def main():
    results = [-1, -2, -3]

    run_number = 0

    while len(set(results)) > 1:
        run_number += 1
        result = run(run_number, number_of_updates=50 ** 6)
        results = results[1:] + [result]


def run(run_number, number_of_updates):
    print('Run number %d...' % (run_number,))

    NUMBER_OF_INSTRUMENTS = 10
    POISON_PILL = -1

    buffer = CoalescingRingBuffer(1 << 20)
    read_counter = [0]

    stop_watch = StopWatch()
    producer_thread = Thread(
        target=producer,
        args=(stop_watch, NUMBER_OF_INSTRUMENTS, POISON_PILL, number_of_updates, buffer))
    consumer_thread = Thread(
        target=consumer,
        args=(stop_watch, NUMBER_OF_INSTRUMENTS, POISON_PILL, read_counter, buffer))

    gc.collect()

    producer_thread.daemon = True
    consumer_thread.daemon = True

    producer_thread.start()
    consumer_thread.start()

    while consumer_thread.is_alive():
        sleep(0.5)

    nanos_taken = stop_watch.nanos_taken

    print('Total run time: %.2f s' % (nanos_taken * NANO,))
    print('Compression ratio: %.2f' % (number_of_updates / read_counter[0],))

    mega_ops_per_second = round(1000 * number_of_updates / nanos_taken, 2)
    print('MOPS: %.2f' % (mega_ops_per_second,))
    return mega_ops_per_second


def producer(stop_watch, number_of_instruments, poison_pill, number_of_updates, buffer):
    def calculate_id(counter):
        for i in xrange(1, number_of_instruments):
            if counter & 1 == 1:
                return i

            counter >>= 1

        return number_of_instruments

    snapshots = [(i, i * 2) for i in xrange(number_of_instruments)]

    current_snapshot = [0]

    def next_snapshot():
        current_snapshot[0] += 1
        if current_snapshot[0] == number_of_instruments:
            current_snapshot[0] = 0

        return snapshots[current_snapshot[0]]

    def put(id, item):
        success = buffer.offer(id, item)
        assert success, 'Failed to add %r with id %d' % (item, id)

    stop_watch.producer_started()

    for i in xrange(number_of_updates):
        put(calculate_id(i), next_snapshot())

    put(poison_pill, poison_pill)
    print('producer stop')


def consumer(stop_watch, number_of_instruments, poison_pill, read_counter, buffer):
    stop_watch.consumer_started()

    rc = 0

    while True:
        bucket = []
        buffer.poll(bucket)

        for element in bucket:
            if element == poison_pill:
                print('consumer stop')
                read_counter[0] = rc
                stop_watch.consumer_stopped()
                return

            rc += 1

        sleep_until = time() + 10 * 1000 * NANO
        while time() < sleep_until:
            pass


if __name__ == '__main__':
    main()
