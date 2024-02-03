from copy import deepcopy

from ..numpyarray import NumpyArray


class NetCDFFileMixin:
    """Mixin class for netCDF file arrays.

    .. versionadded:: (cfdm) HDFVER

    """

    def _get_attr(self, var, attr):
        """Get a variable attribute.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

            var:
                The variable.

            attr: `str`
                The attribute name.

        :Returns:

            The attirbute value.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}._get_attr"
        )  # pragma: no cover

    def _group(self, dataset, groups):
        """Retrun the group object containing a variable.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

            dataset: `netCDF4.Dataset` or `h5netcdf.File`
                The dataset containging the variable.

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

    def _set_units(self, var):
        """The units and calendar properties.

        These are set from the netCDF variable attributes, but only if
        they have already not been defined, either during {{class}}
        instantiation or by a previous call to `_set_units`.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable containing the units and calendar
                definitions.

        :Returns:

            `tuple`
                The units and calendar values, either of which may be
                `None`.

        """
        # Note: Can't use None as the default since it is a valid
        #       `units` or 'calendar' value that indicates that the
        #       attribute has not been set in the dataset.
        units = self._get_component("units", False)
        if units is False:
            try:
                units = self._get_attr(var, "units")
            except AttributeError:
                units = None

            self._set_component("units", units, copy=False)

        calendar = self._get_component("calendar", False)
        if calendar is False:
            try:
                calendar = self._get_attr(var, "calendar")
            except AttributeError:
                calendar = None

            self._set_component("calendar", calendar, copy=False)

        return units, calendar

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
                The dataset to be be closed.

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

    def get_missing_values(self):
        """The missing value indicators from the netCDF variable.

        .. versionadded:: (cfdm) 1.10.0.3

        :Returns:

            `dict` or `None`
                The missing value indicators from the netCDF variable,
                keyed by their netCDF attribute names. An empty
                dictionary signifies that no missing values are given
                in the file. `None` signifies that the missing values
                have not been set.

        **Examples**

        >>> a.get_missing_values()
        None

        >>> b.get_missing_values()
        {}

        >>> c.get_missing_values()
        {'missing_value': 1e20, 'valid_range': (-10, 20)}

        >>> d.get_missing_values()
        {'valid_min': -999}

        """
        out = self._get_component("missing_values", None)
        if out is None:
            return

        return out.copy()

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The new with all of its data in memory.

        """
        return NumpyArray(self[...])
