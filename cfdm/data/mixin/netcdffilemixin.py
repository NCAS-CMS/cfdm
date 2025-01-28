from ..numpyarray import NumpyArray


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class NetCDFFileMixin:
    """Mixin class for netCDF file arrays.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    def _group(self, dataset, groups):
        """Return the group object containing a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dataset: `netCDF4.Dataset` or `h5netcdf.File`
                The dataset containing the variable.

            groups: sequence of `str`
                The definition of which group the variable is in. For
                instance, of the variable is in group
                ``/forecast/model`` then *groups* would be
                ``['forecast', 'model']``.

        :Returns:

            `netCDF4.Dataset` or `netCDF4.Group`
             or `h5netcdf.File` or `h5netcdf.Group`
                The group object, which might be the root group.

        """
        for g in groups:
            dataset = dataset.groups[g]

        return dataset

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during {{class}}
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}._set_attributes"
        )  # pragma: no cover

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

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dataset:
                The dataset to be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

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

    def get_mask(self):
        """Whether or not to automatically mask the data.

        .. versionadded:: (cfdm) 1.8.2

        **Examples**

        >>> b = a.get_mask()

        """
        return self._get_component("mask")

    def get_missing_values(self, default=ValueError()):
        """The missing value indicators from the netCDF variable.

        Deprecated at version 1.11.2.0. Use `get_attributes` instead.

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
        raise DeprecationError(
            f"{self.__class__.__name__}.get_missing_values was deprecated "
            "at version 1.11.2.0 and is no longer available. "
            f"Use {self.__class__.__name__}.get_attributes instead."
        )

    def get_unpack(self):
        """Whether or not to automatically unpack the data.

        .. versionadded:: (cfdm) 1.11.2.0

        **Examples**

        >>> a.get_unpack()
        True

        """
        return self._get_component("unpack")

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The new array with all of its data in memory.

        """
        return NumpyArray(self[...])
