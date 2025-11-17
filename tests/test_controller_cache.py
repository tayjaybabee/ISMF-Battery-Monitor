from ismf_battery_monitor.controllers.cache import ControllerCache


class DummyController:
    def __init__(self, port_name):
        self.port_name = port_name


def test_controller_cache_empty_first_last():
    cache = ControllerCache()
    cache.clear()

    assert cache.first() is None
    assert cache.last() is None


def test_controller_cache_remove_where_empty():
    cache = ControllerCache()
    cache.clear()

    assert cache.remove_where(lambda _: True) == 0


def test_controller_cache_uniqueness():
    cache = ControllerCache()
    cache.clear()

    a = DummyController('left')
    b = DummyController('right')
    dup = DummyController('left')

    cache.add(a)
    cache.add(b)
    cache.add(dup)

    assert len(cache) == 2
    assert cache.first() is a
    assert cache.last() is b


def test_controller_cache_remove_where():
    cache = ControllerCache()
    cache.clear()

    cache.extend([DummyController('one'), DummyController('two')])
    removed = cache.remove_where(lambda c: c.port_name == 'one')

    assert removed == 1
    assert len(cache) == 1
    assert cache.first().port_name == 'two'


def test_controller_cache_remove_where_no_match():
    cache = ControllerCache()
    cache.clear()

    cache.extend([DummyController('alpha'), DummyController('beta')])
    removed = cache.remove_where(lambda c: c.port_name == 'gamma')

    assert removed == 0
    assert len(cache) == 2


def test_controller_cache_remove_where_multiple_matches():
    cache = ControllerCache()
    cache.clear()
    cache.key_fn = lambda c: id(c)

    cache.extend([
        DummyController('shared'),
        DummyController('shared'),
        DummyController('unique'),
    ])

    removed = cache.remove_where(lambda c: c.port_name == 'shared')

    assert removed == 2
    assert len(cache) == 1
    assert cache.first().port_name == 'unique'

    cache.key_fn = lambda c: getattr(c, 'port_name', id(c))
