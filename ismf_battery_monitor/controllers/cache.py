# Author: Taylor-Jayde Blackstone (Inspyre Softworks)
# Project: IS-Matrix-Forge – Controller Cache
# File: cache.py
#
# Description:
#     A singleton, list-like cache for LEDMatrixController instances.
#     Ensures uniqueness while preserving insertion order.
#
# Dependencies:
#     threading
#
# Example Usage:
#     cache = ControllerCache()
#     cache.extend(get_controllers(...))
#     for c in cache: ...
#     left = cache[0] if len(cache) else None

from __future__ import annotations

from threading import Lock
from typing import Callable, Iterable, Iterator, List, Optional, TypeVar, Generic

T = TypeVar('T')


class ControllerCache(Generic[T]):
    """
    A singleton, list-like cache that maintains unique items in insertion order.

    Uniqueness is enforced via a configurable identity function. By default,
    identity is object identity (`id(obj)`), which is robust if the underlying
    objects do not implement `__eq__`. If your controllers expose a stable,
    unique attribute (e.g., `serial`), provide `key_fn=lambda c: c.serial`.

    Parameters:
        key_fn (Callable[[T], object], optional):
            Function that returns a unique, hashable key for an item. Defaults
            to `id`.

    Properties:
        key_fn (Callable[[T], object]):
            The identity function currently used to deduplicate entries.

    Methods:
        add(item): Add a single item if not present.
        extend(items): Add multiple items, preserving order and uniqueness.
        clear(): Empty the cache.
        get(): Return a shallow copy of the underlying list.
        first(): Return the first item or None.
        last(): Return the last item or None.
        remove_where(pred): Remove items matching predicate.

    Example Usage:
        >>> cache = ControllerCache()  # singleton
        >>> cache.add(controller)
        >>> len(cache)
        1
        >>> cache.key_fn = lambda c: c.serial  # switch to serial-based identity

    Notes:
        This class is a process-local singleton. All imports in the same
        interpreter will see the same instance.
    """

    _instance: Optional['ControllerCache[T]'] = None
    _init_lock = Lock()

    def __new__(cls, *args, **kwargs):
        # Double-checked locking to keep init minimal and safe.
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Internal init placeholders; __init__ sets real values.
                    cls._instance._items = []  # type: ignore[attr-defined]
                    cls._instance._keys = set()  # type: ignore[attr-defined]
                    cls._instance._lock = Lock()  # type: ignore[attr-defined]
                    cls._instance._key_fn = id  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self, key_fn: Optional[Callable[[T], object]] = None):
        if key_fn is None:
            key_fn = lambda c: getattr(c, 'port_name', id(c))

        self.key_fn = key_fn

    # ----- Core list-like protocol -----------------------------------------

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)  # type: ignore[attr-defined]

    def __getitem__(self, idx: int) -> T:
        return self._items[idx]  # type: ignore[attr-defined]

    def __len__(self) -> int:
        return len(self._items)  # type: ignore[attr-defined]

    # ----- Configuration -----------------------------------------------------

    @property
    def key_fn(self) -> Callable[[T], object]:
        return self._key_fn  # type: ignore[attr-defined]

    @key_fn.setter
    def key_fn(self, fn: Callable[[T], object]) -> None:
        """
        Change the identity function and re-index existing items.

        Raises:
            ValueError: If the new key function creates duplicate keys for items
                        already in the cache.
        """
        with self._lock:  # type: ignore[attr-defined]
            new_keys = set()
            for item in self._items:  # type: ignore[attr-defined]
                k = fn(item)
                if k in new_keys:
                    raise ValueError('Changing key_fn would introduce duplicates.')
                new_keys.add(k)
            self._key_fn = fn  # type: ignore[attr-defined]
            self._keys = new_keys  # type: ignore[attr-defined]

    # ----- Mutators ---------------------------------------------------------

    def add(self, item: T) -> None:
        """
        Add an item if not already present (by key).

        Parameters:
            item (T):
                The item to add.
        """
        k = self.key_fn(item)
        with self._lock:  # type: ignore[attr-defined]
            if k not in self._keys:  # type: ignore[attr-defined]
                self._items.append(item)  # type: ignore[attr-defined]
                self._keys.add(k)  # type: ignore[attr-defined]

    def extend(self, items: Iterable[T]) -> None:
        """
        Add multiple items, preserving order and uniqueness.

        Parameters:
            items (Iterable[T]):
                Items to add.
        """
        for it in items:
            self.add(it)

    def clear(self) -> None:
        """Remove all items from the cache."""
        with self._lock:  # type: ignore[attr-defined]
            self._items.clear()  # type: ignore[attr-defined]
            self._keys.clear()  # type: ignore[attr-defined]

    def remove_where(self, pred: Callable[[T], bool]) -> int:
        """
        Remove items that match the predicate.

        Parameters:
            pred (Callable[[T], bool]):
                Function returning True for items to remove.

        Returns:
            int: Number of removed items.
        """
        removed = 0
        with self._lock:  # type: ignore[attr-defined]
            keep_items: List[T] = []
            keep_keys = set()
            for it in self._items:  # type: ignore[attr-defined]
                if pred(it):
                    removed += 1
                    continue
                keep_items.append(it)
                keep_keys.add(self.key_fn(it))
            self._items = keep_items  # type: ignore[attr-defined]
            self._keys = keep_keys  # type: ignore[attr-defined]
        return removed

    # ----- Convenience ------------------------------------------------------

    def get(self) -> List[T]:
        """Return a shallow copy of the cache contents."""
        return list(self._items)  # type: ignore[attr-defined]

    def first(self) -> Optional[T]:
        """Return the first item, or None if empty."""
        return self._items[0] if self._items else None  # type: ignore[attr-defined]

    def last(self) -> Optional[T]:
        """Return the last item, or None if empty."""
        return self._items[-1] if self._items else None  # type: ignore[attr-defined]
