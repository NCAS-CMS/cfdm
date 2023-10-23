import functools


class cached_property(functools.cached_property):
    """Read only version of functools.cached_property."""

    def __set__(self, instance, val):
        """Raise an error when attempting to set a cached property."""
        raise AttributeError("Can't set attribute")
