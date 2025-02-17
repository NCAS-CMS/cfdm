class DeprecationError(Exception):
    """Deprecation error."""

    pass


class NumpyArray:
    """An underlying `numpy` array.

    Deprecated at version NEXTVERSION and is no longer available. Use
    `numpy` instead.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, *args, **kwargs):
        """**Initialisation**"""
        raise DeprecationError(
            f"{self.__class__.__name__} was deprecated at version NEXTVERSION "
            "and is no longer available. Use numpy instead."
        )
