class ZarrDimension:
    """TODOZARR.

    The current maximum size of the dimension can be obtained by
    calling the python `len` function on the `ZarrDimension`
    instance. The `isunlimited` method of a `Dimension` instance can
    be used to determine if the dimension is unlimited.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(self, name, size):
        """TODOZARR."""
        self.name = name
        self.size = size

    def __len__(self):
        """TODOZARR."""
        return self.size

    def isunlimited(self):
        """Whether or not the dimension is unlimited.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `bool`
                `True` if and only if the dimension is unlimited.

        """
        return False
