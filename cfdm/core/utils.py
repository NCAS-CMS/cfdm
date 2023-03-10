"""Read only version of functools.cached_property.

Copied from dask https://github.com/dask/dask/blob/dfdde1c9e666d5830f
7a8df53160aca6ff1b881f/dask/utils.py.

When Python 3.7 is deprecated, we can remove the _cached_property class.

"""
import functools
from _thread import RLock

try:
    _cached_property = functools.cached_property  # Only from Python 3.8
except AttributeError:
    # TODO: Copied from functools.cached_property in python
    #       3.8. Remove when minimum supported python version is 3.8:
    _NOT_FOUND = object()

    class _cached_property:
        def __init__(self, func):
            self.func = func
            self.attrname = None
            self.__doc__ = func.__doc__
            self.lock = RLock()

        def __set_name__(self, owner, name):
            if self.attrname is None:
                self.attrname = name
            elif name != self.attrname:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    f"({self.attrname!r} and {name!r})."
                )

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            if self.attrname is None:
                raise TypeError(
                    "Cannot use cached_property instance without calling __set_name__ on it."
                )
            try:
                cache = instance.__dict__
            except (
                AttributeError
            ):  # not all objects have __dict__ (e.g. class defines slots)
                msg = (
                    f"No '__dict__' attribute on {type(instance).__name__!r} "
                    f"instance to cache {self.attrname!r} property."
                )
                raise TypeError(msg) from None
            val = cache.get(self.attrname, _NOT_FOUND)
            if val is _NOT_FOUND:
                with self.lock:
                    # check if another thread filled cache while we awaited lock
                    val = cache.get(self.attrname, _NOT_FOUND)
                    if val is _NOT_FOUND:
                        val = self.func(instance)
                        try:
                            cache[self.attrname] = val
                        except TypeError:
                            msg = (
                                f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                                f"does not support item assignment for caching {self.attrname!r} property."
                            )
                            raise TypeError(msg) from None
            return val


class cached_property(_cached_property):
    """Read only version of functools.cached_property."""

    def __set__(self, instance, val):
        """Raise an error when attempting to set a cached property."""
        raise AttributeError("Can't set attribute")
