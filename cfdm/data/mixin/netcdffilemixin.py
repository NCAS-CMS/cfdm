from ..numpyarray import NumpyArray


class NetCDFFileMixin:
    """Mixin class for netCDF file arrays.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    # ef close(self, dataset):
    #   """Close the dataset containing the data.
    #
    #   .. versionadded:: (cfdm) 1.7.0
    #
    #   :Parameters:
    #
    #       dataset:
    #           The dataset to be closed.
    #
    #   :Returns:
    #
    #       `None`
    #
    #   """
    #   if self._get_component("close"):
    #       dataset.close()

    def get_format(self):
        """The format of the files.

        .. versionadded:: (cfdm) 1.10.1.0

        .. seealso:: `get_address`, `get_filename`, `get_formats`

        :Returns:

            `str`
                The file format. Always ``'nc'``, signifying netCDF.

        **Examples**

        >>> a.get_format()
        'nc'

        """
        return "nc"

    def get_missing_values(self, default=ValueError()):
        """The missing value indicators from the netCDF variable.

        Deprecated at version NEXTVERSION. Use `get_attributes` instead.

        .. versionadded:: (cfdm) 1.10.0.3

        :Parameters:

            default: optional
                Return the value of the *default* parameter if no missing
                values have yet been defined.

                {{default Exception}}

        :Returns:

            `dict` or `None`
                The missing value indicators from the netCDF variable,
                keyed by their netCDF attribute names. An empty
                dictionary signifies that no missing values are given
                in the file. `None` signifies that the missing values
                have not been set.

        **Examples**

        >>> a.get_missing_values(None)
        None

        >>> b.get_missing_values({})
        {}

        >>> b.get_missing_values()
        {}

        >>> c.get_missing_values()
        {'missing_value': 1e20, 'valid_range': (-10, 20)}

        >>> d.get_missing_values()
        {'valid_min': -999}

        """

        class DeprecationError(Exception):
            """Deprecation error."""

            pass

        raise DeprecationError(
            f"{self.__class__.__name__}.get_missing_values was deprecated "
            "at version NEXTVERSION and is no longer available. "
            f"Use {self.__class__.__name__}.get_attributes instead."
        )

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The new array with all of its data in memory.

        """
        return NumpyArray(self[...])
