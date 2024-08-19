from ..numpyarray import NumpyArray


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class NetCDFFileMixin:
    """Mixin class for netCDF file arrays.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        unpack=True,
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

            {{init mask: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.2

            {{init unpack: `bool`, optional}}

                .. versionadded:: (cfdm) NEXTVERSION

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from the netCDF variable during
                the first `__getitem__` call.

                .. versionadded:: (cfdm) NEXTVERSION

            {{init storage_options: `dict` or `None`, optional}}

                .. versionadded:: (cfdm) NEXTVERSION

            {{init source: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            {{init copy: `bool`, optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            missing_values: Deprecated at version NEXTVERSION
                The missing value indicators defined by the netCDF
                variable attributes. They may now be recorded via the
                *attributes* parameter

            ncvar:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            varid:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            group: Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            units: `str` or `None`, optional
                Deprecated at version NEXTVERSION. Use the
                *attributes* parameter instead.

            calendar: `str` or `None`, optional
                Deprecated at version NEXTVERSION. Use the
                *attributes* parameter instead.

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                shape = source._get_component("shape", None)
            except AttributeError:
                shape = None

            try:
                filename = source._get_component("filename", None)
            except AttributeError:
                filename = None

            try:
                address = source._get_component("address", None)
            except AttributeError:
                address = None

            try:
                dtype = source._get_component("dtype", None)
            except AttributeError:
                dtype = None

            try:
                mask = source._get_component("mask", True)
            except AttributeError:
                mask = True

            try:
                unpack = source._get_component("unpack", True)
            except AttributeError:
                unpack = True

            try:
                attributes = source._get_component("attributes", None)
            except AttributeError:
                attributes = None

            try:
                storage_options = source._get_component(
                    "storage_options", None
                )
            except AttributeError:
                storage_options = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            if isinstance(filename, str):
                filename = (filename,)
            else:
                filename = tuple(filename)

            self._set_component("filename", filename, copy=False)

        if address is not None:
            if isinstance(address, (str, int)):
                address = (address,)
            else:
                address = tuple(address)

            self._set_component("address", address, copy=False)

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", bool(mask), copy=False)
        self._set_component("unpack", bool(unpack), copy=False)
        self._set_component("storage_options", storage_options, copy=False)
        self._set_component("attributes", attributes, copy=False)

        # By default, close the netCDF file after data array access
        self._set_component("close", True, copy=False)

    def _group(self, dataset, groups):
        """Return the group object containing a variable.

        .. versionadded:: (cfdm) NEXTVERSION

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

        .. versionadded:: (cfdm) NEXTVERSION

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
        raise DeprecationError(
            f"{self.__class__.__name__}.get_missing_values was deprecated "
            "at version NEXTVERSION and is no longer available. "
            f"Use {self.__class__.__name__}.get_attributes instead."
        )

    def get_unpack(self):
        """Whether or not to automatically unpack the data.

        .. versionadded:: (cfdm) NEXTVERSION

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
