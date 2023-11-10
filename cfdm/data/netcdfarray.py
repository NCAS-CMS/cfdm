import netCDF4
import numpy

from . import abstract
from .mixin import FileArrayMixin
from .numpyarray import NumpyArray


class NetCDFArray(FileArrayMixin, abstract.Array):
    """An underlying array stored in a netCDF file.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        units=False,
        calendar=False,
        missing_values=None,
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

            mask: `bool`
                If True (the default) then mask by convention when
                reading data from disk.

                A netCDF array is masked depending on the values of any of
                the netCDF variable attributes ``valid_min``,
                ``valid_max``, ``valid_range``, ``_FillValue`` and
                ``missing_value``.

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

            missing_values: `dict`, optional
                The missing value indicators defined by the netCDF
                variable attributes. See `get_missing_values` for
                details.

                .. versionadded:: (cfdm) 1.10.0.3

            {{init source: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            {{init copy: `bool`, optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            ncvar:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            varid:  Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

            group: Deprecated at version 1.10.1.0
                Use the *address* parameter instead.

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
                units = source._get_component("units", False)
            except AttributeError:
                units = False

            try:
                calendar = source._get_component("calendar", False)
            except AttributeError:
                calendar = False

            try:
                missing_values = source._get_component("missing_values", None)
            except AttributeError:
                missing_values = None

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

        if missing_values is not None:
            self._set_component(
                "missing_values", missing_values.copy(), copy=False
            )

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", mask, copy=False)
        self._set_component("units", units, copy=False)
        self._set_component("calendar", calendar, copy=False)

        # By default, close the netCDF file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        The indices that define the subspace must be either `Ellipsis` or
        a sequence that contains an index for each dimension. In the
        latter case, each dimension's index must either be a `slice`
        object or a sequence of two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        .. versionadded:: (cfdm) 1.7.0

        """
        netcdf, address = self.open()
        dataset = netcdf

        mask = self.get_mask()
        groups, address = self.get_groups(address)

        if groups:
            # Traverse the group structure, if there is one (CF>=1.8).
            for g in groups[:-1]:
                netcdf = netcdf.groups[g]

            netcdf = netcdf.groups[groups[-1]]

        if isinstance(address, str):
            # Get the variable by netCDF name
            variable = netcdf.variables[address]
            variable.set_auto_mask(mask)
            array = variable[indices]
        else:
            # Get the variable by netCDF integer ID
            for variable in netcdf.variables.values():
                if variable._varid == address:
                    variable.set_auto_mask(mask)
                    array = variable[indices]
                    break

        # Set the units, if they haven't been set already.
        self._set_units(variable)

        self.close(dataset)
        del netcdf, dataset

        string_type = isinstance(array, str)
        if string_type:
            # --------------------------------------------------------
            # A netCDF string type scalar variable comes out as Python
            # str object, so convert it to a numpy array.
            # --------------------------------------------------------
            array = numpy.array(array, dtype=f"U{len(array)}")

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1, 1d
            array = array.squeeze()

        kind = array.dtype.kind
        if not string_type and kind in "SU":
            #     == 'S' and array.ndim > (self.ndim -
            #     getattr(self, 'gathered', 0) -
            #     getattr(self, 'ragged', 0)):
            # --------------------------------------------------------
            # Collapse (by concatenation) the outermost (fastest
            # varying) dimension of char array into
            # memory. E.g. [['a','b','c']] becomes ['abc']
            # --------------------------------------------------------
            if kind == "U":
                array = array.astype("S", copy=False)

            array = netCDF4.chartostring(array)
            shape = array.shape
            array = numpy.array([x.rstrip() for x in array.flat], dtype="U")
            array = numpy.reshape(array, shape)
            array = numpy.ma.masked_where(array == "", array)
        elif not string_type and kind == "O":
            # --------------------------------------------------------
            # A netCDF string type N-d (N>=1) variable comes out as a
            # numpy object array, so convert it to numpy string array.
            # --------------------------------------------------------
            array = array.astype("U", copy=False)

            # --------------------------------------------------------
            # netCDF4 does not auto-mask VLEN variable, so do it here.
            # --------------------------------------------------------
            array = numpy.ma.where(array == "", numpy.ma.masked, array)

        return array

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        return f"{self.get_filename(None)}, {self.get_address()}"

    def _set_units(self, var):
        """The units and calendar properties.

        These are set from the netCDF variable attributes, but only if
        they have already not been defined, either during {{class}}
        instantiation or by a previous call to `_set_units`.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            var: `netCDF4.Variable`
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
                units = var.getncattr("units")
            except AttributeError:
                units = None

            self._set_component("units", units, copy=False)

        calendar = self._get_component("calendar", False)
        if calendar is False:
            try:
                calendar = var.getncattr("calendar")
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

    def get_groups(self, address):
        """The netCDF4 group structure of a netCDF variable.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            address: `str` or `int`
                The netCDF variable name, or integer varid, from which
                to get the groups.

                .. versionadded:: (cfdm) 1.10.1.0

        :Returns:

            (`list`, `str`) or (`list`, `int`)
                The group structure and the name within the group. If
                *address* is a varid then an empty list and the varid
                are returned.

        **Examples**

        >>> n.get_groups('tas')
        ([], 'tas')

        >>> n.get_groups('/tas')
        ([], 'tas')

        >>> n.get_groups('/data/model/tas')
        (['data', 'model'], 'tas')

        >>> n.get_groups(9)
        ([], 9)

        """
        try:
            if "/" not in address:
                return [], address
        except TypeError:
            return [], address

        out = address.split("/")[1:]
        return out[:-1], out[-1]

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

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dataset: `netCDF4.Dataset`
                The netCDF dataset to be be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def open(self):
        """Return an open file object containing the data array.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and an open file object is
        returned from the first file that exists.

        :Returns:

            (`netCDF4.Dataset`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(netCDF4.Dataset, mode="r")

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The new with all of its data in memory.

        """
        return NumpyArray(self[...])
