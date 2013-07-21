from __future__ import with_statement

from nose.tools import eq_, ok_

from coalringbuf import CoalescingRingBuffer


def not_(expr, msg=None):
    ok_(not expr, msg)


def create_buffer(capacity):
    return CoalescingRingBuffer(capacity)


def add_key_and_value(buffer, key, value):
    ok_(buffer.offer(key, value))


def add_value(buffer, value):
    ok_(buffer.offer(value))


def assert_contains(buffer, *args):
    bucket = []

    buffer.poll(bucket)
    eq_(bucket, list(args))
    ok_(buffer.empty)


def test_should_correctly_increase_the_capacity_to_the_next_higher_power_of_two():
    for requested_capacity, result_capacity in ((15, 16), (16, 16), (17, 32)):
        yield check_capacity, requested_capacity, result_capacity


def check_capacity(requested_capacity, capacity):
    buffer = create_buffer(requested_capacity)
    eq_(buffer.capacity, capacity)


def test_should_correctly_report_size():
    bucket = []
    buffer = CoalescingRingBuffer(2)

    eq_(buffer.size, 0)
    ok_(buffer.empty)
    not_(buffer.full)

    buffer.offer('asd')

    eq_(buffer.size, 1)
    not_(buffer.empty)
    not_(buffer.full)

    buffer.offer(1, 'qwe')

    eq_(buffer.size, 2)
    not_(buffer.empty)
    ok_(buffer.full)

    fetched = buffer.poll(bucket, 1)

    eq_(fetched, 1)
    eq_(buffer.size, 1)
    not_(buffer.empty)
    not_(buffer.full)

    fetched = buffer.poll(bucket, 1)

    eq_(fetched, 1)
    eq_(buffer.size, 0)
    ok_(buffer.empty)
    not_(buffer.full)


def test_should_reject_values_without_keys_when_full():
    buffer = create_buffer(2)
    for i in range(2):
        buffer.offer(i)

    result = buffer.offer('x')
    not_(result)
    eq_(buffer.size, 2)


def test_should_reject_new_keys_when_full():
    buffer = create_buffer(2)
    for i in range(2):
        buffer.offer(i, i)

    result = buffer.offer(4, 4)
    not_(result)
    eq_(buffer.size, 2)


def test_should_accept_existing_keys_when_full():
    buffer = create_buffer(2)
    for i in range(2):
        buffer.offer(i, i)

    result = buffer.offer(1, 314)
    ok_(result)
    eq_(buffer.size, 2)


def test_should_return_single_value():
    buffer = create_buffer(2)
    add_key_and_value(buffer, 1, '1')
    assert_contains(buffer, '1')


def test_should_return_two_values_with_different_keys():
    buffer = create_buffer(2)
    add_key_and_value(buffer, 1, '1')
    add_key_and_value(buffer, 2, '2')

    assert_contains(buffer, '1', '2')


def test_should_update_values_with_equal_keys():
    buffer = create_buffer(2)
    add_key_and_value(buffer, 1, '1a')
    add_key_and_value(buffer, 1, '1b')

    assert_contains(buffer, '1b')


def test_should_not_update_values_without_keys():
    buffer = create_buffer(2)
    add_value(buffer, '1a')
    add_value(buffer, '1b')

    assert_contains(buffer, '1a', '1b')


def test_should_update_values_with_equal_keys_and_preserve_ordering():
    buffer = create_buffer(8)

    for key, value in (
            (1, '1a'),
            (2, '2'),
            (1, '1b')
    ):
        add_key_and_value(buffer, key, value)

    assert_contains(buffer, '1b', '2')


def test_should_not_update_values_if_read_occurs_between_values():
    buffer = create_buffer(2)

    add_key_and_value(buffer, 1, '1a')
    assert_contains(buffer, '1a')

    add_key_and_value(buffer, 1, '1b')
    assert_contains(buffer, '1b')


def test_should_return_only_the_maximum_number_of_requested_items():
    buffer = create_buffer(8)

    for value in ('2', '1a', '1b'):
        add_value(buffer, value)

    bucket = []
    eq_(buffer.poll(bucket, 2), 2)
    eq_(len(bucket), 2)
    eq_(bucket, ['2', '1a'])

    bucket[:] = []
    eq_(buffer.poll(bucket, 1), 1)
    eq_(len(bucket), 1)
    eq_(bucket, ['1b'])

    ok_(buffer.empty)


def test_should_return_all_items_without_request_limit():
    buffer = create_buffer(8)

    add_value(buffer, '2')
    add_key_and_value(buffer, 1, '1a')
    add_key_and_value(buffer, 1, '1b')

    bucket = []

    eq_(buffer.poll(bucket), 2)
    eq_(len(bucket), 2)
    eq_(bucket, ['2', '1b'])

    ok_(buffer.empty)


def test_should_count_rejections():
    buffer = create_buffer(2)
    eq_(buffer.rejection_count, 0)

    buffer.offer('x')
    eq_(buffer.rejection_count, 0)

    buffer.offer(1, 'x')
    eq_(buffer.rejection_count, 0)

    buffer.offer(1, 'x')
    eq_(buffer.rejection_count, 0)

    buffer.offer('x')
    eq_(buffer.rejection_count, 1)

    buffer.offer(2, 'x')
    eq_(buffer.rejection_count, 2)


def test_should_use_object_equality_to_compare_keys():
    buffer = create_buffer(8)

    buffer.offer(['this', 'is', 'a', 'key'], 'x')
    buffer.offer(['this', 'is', 'a', 'key'], 'y')

    eq_(buffer.size, 1)
