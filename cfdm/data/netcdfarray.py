class DeprecationError(Exception):
    """Deprecation error."""

    pass


class NetCDFArray:
    """A netCDF array accessed with `netCDF4`.

    Deprecated at version 1.11.2.0 and is no longer available. Use
    `cfdm.NetCDF4Array` instead.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        unpack=True,
        units=False,
        calendar=False,
        attributes=None,
        storage_options=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of) `str`, optional
                The name of the netCDF file(s) containing the array.

            address: (sequence of) `str` or `int`, optional
                The identity of the netCDF variable in each file
                defined by *filename*. Either a netCDF variable name
                or an integer netCDF variable ID.

                .. versionadded:: (cfdm) 1.10.1.0

            dtype: `numpy.dtype`
                The data type of the array in the netCDF file. May be
                `None` if the numpy data-type is not known (which can be
                the case for netCDF string types, for example).

            shape: `tuple`
                The array dimension sizes in the netCDF file.

            size: `int`
                Number of elements in the array in the netCDF file.

            ndim: `int`
                The number of array dimensions in the netCDF file.

            {{init mask: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.2

            units: `str` or `None`, optional
                The units of the netCDF variable. Set to `None` to
                indicate that there are no units. If unset then the
                units will be set during the first `__getitem__` call.

                .. versionadded:: (cfdm) 1.10.0.1

            calendar: `str` or `None`, optional
                The calendar of the netCDF variable. By default, or if
                set to `None`, then the CF default calendar is
                assumed, if applicable. If unset then the calendar
                will be set during the first `__getitem__` call.

                .. versionadded:: (cfdm) 1.10.0.1

            {{init source: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            {{init copy: `bool`, optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            missing_values: Deprecated at version 1.11.2.0
                The missing value indicators defined by the netCDF
                variable attributes. They may now be recorded via the
                *attributes* parameter

            ncvar:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            varid:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            group: Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

        """
        raise DeprecationError(
            f"{self.__class__.__name__} was deprecated at version 1.11.2.0 "
            "and is no longer available. Use cfdm.NetCDF4Array instead."
        )
