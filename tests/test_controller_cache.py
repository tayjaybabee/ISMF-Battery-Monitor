from ismf_battery_monitor.controllers.cache import ControllerCache


class DummyController:
    def __init__(self, port_name):
        self.port_name = port_name


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
