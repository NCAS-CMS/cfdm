from .propertiesdata import PropertiesData


class Topology(PropertiesData):
    """Abstract base class for topology-related constructs.

    .. versionadded:: (cfdm) UGRIDVER

    """

    @property
    def ndim(self):
        """The number of data dimensions.

        Only the data dimensions that corresponds to a domain axis
        construct is included.

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `data`, `has_data`, `shape`, `size`

        **Examples**

        >>> d.shape
        (1324,)
        >>> d.ndim
        1
        >>> f.size
        1324

        """
        try:
            return len(self.shape)
        except AttributeError:
            raise AttributeError(
                f"{self.__class__.__name__} object has no attribute 'ndim'"
            )

    @property
    def shape(self):
        """A tuple of the data array's dimension sizes.

        Only the data dimension that corresponds to a domain axis
        construct is included.

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `data`, `has_data`, `ndim`, `size`

        **Examples**

        >>> d.shape
        (1324,)
        >>> d.ndim
        1
        >>> d.size
        1324

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            return data.shape[:1]

        raise AttributeError(
            f"{self.__class__.__name__} object has no attribute 'shape'"
        )

    @property
    def size(self):
        """The number elements in the data.

        `size` is equal to the product of `shape`, that only includes
        the data dimension corresponding to a domain axis construct.

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `data`, `has_data`, `ndim`, `shape`

        **Examples**

        >>> d.shape
        (1324,)
        >>> d.ndim
        1
        >>> d.size
        1324

        """
        try:
            return self.shape[0]
        except AttributeError:
            raise AttributeError(
                f"{self.__class__.__name__} object has no attribute 'size'"
            )
