from abc import ABCMeta
from threading import Lock


class SingletonABCMeta(ABCMeta):
    """
    A metaclass that ensures all subclasses are singletons.

    This metaclass can be combined with abstract base classes
    to make all concrete subclasses singletons.
    """
    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with SingletonABCMeta._lock:
            if cls not in SingletonABCMeta._instances:
                instance = super().__call__(*args, **kwargs)
                SingletonABCMeta._instances[cls] = instance
            return SingletonABCMeta._instances[cls]
