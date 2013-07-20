from six.moves import xrange

__version__ = '0.1.0'


class CoalescingBuffer(object):
    '''
    General CoalescingBuffer interface
    '''

    @property
    def size(self):
        '''
        :returns: number of elements in the buffer
        :rtype: int
        '''

    @property
    def capacity(self):
        '''
        :returns: maximum number of elements in the buffer
        :rtype: int
        '''

    @property
    def empty(self):
        '''
        :returns: true if the buffer is empty, false otherwise
        :rtype: bool
        '''
        pass

    @property
    def full(self):
        '''
        :returns: true if the buffer is full, false otherwise
        :rtype: bool
        '''

    def offer(self, *args):
        '''Add a value to the buffer.

        There are 2 usage scenarios:

        * offer(value) - add a value that will never be collapsed
        * offer(key, value) - add a value to be collapsed on the given key
        :returns: true if value was was added to the buffer, false otherwise
            (this means the buffer was full)
        :rtype: bool
        '''

    def poll(self, bucket, max_items=None):
        '''Fetch items into given bucket.

        :param bucket: container for the items
        :type bucket: :class:`list`
        :param max_items: maximum number of items to read from the buffer. If None,
            all available items will be fetched
        :type max_items: int or None
        :returns: number of items fetched from the buffer
        :rtype: int
        '''


def next_power_of_two(number):
    return 1 << len(bin(number - 1).lstrip('0b'))


class CoalescingRingBuffer(object):
    def __init__(self, capacity):
        '''
        :param capacity: fixed capacity of the buffer, shall be greater than 0;
            it will be rounded up to the next greater or equal power of 2
        :type capacity: int
        '''
        self._capacity = next_power_of_two(capacity)
        self._mask_value = self._capacity - 1
        self._keys = [None] * self._capacity
        self._values = [None] * self._capacity

        # the oldest slot that it's safe to write to
        self._first_write = 1

        # the next write slot
        self._next_write = 1

        # the last cleaned slot
        self._last_cleaned = 0

        # the newest slot that it's safe to write to
        self._last_read = 0

        self._rejection_count = 0

        self._non_collapsible_key = object()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._capacity)

    @property
    def size(self):
        return self._next_write - self._last_read - 1

    @property
    def capacity(self):
        return self._capacity

    @property
    def rejection_count(self):
        return self._rejection_count

    @property
    def empty(self):
        return self._first_write == self._next_write

    @property
    def full(self):
        return self.size == self._capacity

    def offer(self, *args):
        assert len(args) in (1, 2)
        if len(args) == 1:
            key, value = self._non_collapsible_key, args[0]
        else:
            key, value = args

        if key is not self._non_collapsible_key:
            for update_position in xrange(self._first_write, self._next_write):
                index = self._mask(update_position)
                if key == self._keys[index]:
                    self._values[index] = value

                    if update_position >= self._first_write:
                        return True
                    else:
                        break

        return self._add(key, value)

    def _mask(self, value):
        return value & self._mask_value

    def _add(self, key, value):
        if self.full:
            self._rejection_count += 1
            result = False
        else:
            self._clean_up()
            self._store(key, value)
            result = True

        return result

    def _clean_up(self):
        last_read = self._last_read

        if last_read != self._last_cleaned:
            while self._last_cleaned < last_read:
                self._last_cleaned += 1
                index = self._mask(self._last_cleaned)
                self._keys[index] = None
                self._values[index] = None

    def _store(self, key, value):
        index = self._mask(self._next_write)
        self._keys[index] = key
        self._values[index] = value

        self._next_write += 1

    def poll(self, bucket, max_items=None):
        return self._fill(
            bucket,
            min(self._first_write + max_items, self._next_write)
            if max_items
            else self._next_write
        )

    def _fill(self, bucket, claim_up_to):
        self._first_write = claim_up_to
        last_read = self._last_read

        for read_index in xrange(last_read + 1, claim_up_to):
            index = self._mask(read_index)
            bucket.append(self._values[index])

        self._last_read = claim_up_to - 1

        return claim_up_to - last_read - 1
