import netCDF4
import numpy

from . import abstract
from .numpyarray import NumpyArray


class NetCDFArray(abstract.Array):
    """An underlying array stored in a netCDF file.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        filename=None,
        ncvar=None,
        varid=None,
        group=None,
        dtype=None,
        ndim=None,
        shape=None,
        size=None,
        mask=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: `str`
                The name of the netCDF file containing the array.

            ncvar: `str`, optional
                The name of the netCDF variable containing the
                array. Required unless *varid* is set.

            varid: `int`, optional
                The UNIDATA netCDF interface ID of the variable
                containing the array. Required if *ncvar* is not set,
                ignored if *ncvar* is set.

            group: `None` or sequence of `str`, optional
                Specify the netCDF4 group to which the netCDF variable
                belongs. By default, or if *group* is `None` or an
                empty sequence, it assumed to be in the root
                group. The last element in the sequence is the name of
                the group in which the variable lies, with other
                elements naming any parent groups (excluding the root
                group).

                *Parameter example:*
                  To specify that a variable is in the root group:
                  ``group=()`` or ``group=None``

                *Parameter example:*
                  To specify that a variable is in the group '/forecasts':
                  ``group=['forecasts']``

                *Parameter example:*
                  To specify that a variable is in the group
                  '/forecasts/model2': ``group=['forecasts', 'model2']``

                .. versionadded:: (cfdm) 1.8.6.0

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
                If False then do not mask by convention when reading data
                from disk. By default data is masked by convention.

                A netCDF array is masked depending on the values of any of
                the netCDF variable attributes ``valid_min``,
                ``valid_max``, ``valid_range``, ``_FillValue`` and
                ``missing_value``.

                .. versionadded:: (cfdm) 1.8.2

        **Examples:**

        >>> import netCDF4
        >>> nc = netCDF4.Dataset('file.nc', 'r')
        >>> v = nc.variable['tas']
        >>> a = NetCDFFileArray(filename='file.nc', ncvar='tas',
        ...                     group=['forecast'], dtype=v.dtype,
        ...                     ndim=v.ndim, shape=v.shape, size=v.size)

        """
        super().__init__(filename=filename, ncvar=ncvar, varid=varid)

        self._set_component("netcdf", None, copy=False)
        self._set_component("group", group, copy=False)

        # By default, close the netCDF file after data array access
        self._set_component("close", True, copy=False)

        if ndim is not None:
            self._set_component("ndim", ndim, copy=False)

        if size is not None:
            self._set_component("size", size, copy=False)

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", mask, copy=False)

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
        netcdf = self.open()

        # Traverse the group structure, if there is one (CF>=1.8).
        group = self.get_group()
        if group:
            for g in group[:-1]:
                netcdf = netcdf.groups[g]

            netcdf = netcdf.groups[group[-1]]

        ncvar = self.get_ncvar()
        mask = self.get_mask()

        if ncvar is not None:
            # Get the variable by netCDF name
            variable = netcdf.variables[ncvar]
            variable.set_auto_mask(mask)
            array = variable[indices]
        else:
            # Get the variable by netCDF ID
            varid = self.get_varid()

            for variable in netcdf.variables.values():
                if variable._varid == varid:
                    variable.set_auto_mask(mask)
                    array = variable[indices]
                    break

        if self._get_component("close"):
            # Close the netCDF file
            self.close()

        string_type = isinstance(array, str)
        if string_type:
            # --------------------------------------------------------
            # A netCDF string type scalar variable comes out as Python
            # str object, so convert it to a numpy array.
            # --------------------------------------------------------
            array = numpy.array(array, dtype=f"S{len(array)}")

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1 , 1d
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
                array = array.astype("S")

            array = netCDF4.chartostring(array)
            shape = array.shape
            array = numpy.array([x.rstrip() for x in array.flat], dtype="S")
            array = numpy.reshape(array, shape)
            array = numpy.ma.masked_where(array == b"", array)

        elif not string_type and kind == "O":
            # --------------------------------------------------------
            # A netCDF string type N-d (N>=1) variable comes out as a
            # numpy object array, so convert it to numpy string array.
            # --------------------------------------------------------
            array = array.astype("S")  # , copy=False)

            # --------------------------------------------------------
            # netCDF4 does not auto-mask VLEN variable, so do it here.
            # --------------------------------------------------------
            array = numpy.ma.where(array == b"", numpy.ma.masked, array)

        return array

    def __repr__(self):
        """Returns a printable representation of the `NetCDFArray`.

        x.__repr__() is logically equivalent to repr(x)

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Returns a string version of the `NetCDFArray` object.

        x.__str__() is logically equivalent to str(x)

        """
        name = self.get_ncvar()
        if name is None:
            name = f"varid={self.get_varid()}"
        else:
            name = f"variable={name}"

        return f"file={self.get_filename()} {name}"

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        """Data-type of the data elements.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.dtype
        dtype('float64')
        >>> print(type(a.dtype))
        <type 'numpy.dtype'>

        """
        return self._get_component("dtype")

    @property
    def ndim(self):
        """Number of array dimensions.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.shape
        (73, 96)
        >>> a.ndim
        2
        >>> a.size
        7008

        >>> a.shape
        (1, 1, 1)
        >>> a.ndim
        3
        >>> a.size
        1

        >>> a.shape
        ()
        >>> a.ndim
        0
        >>> a.size
        1

        """
        return self._get_component("ndim")

    @property
    def shape(self):
        """Tuple of array dimension sizes.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.shape
        (73, 96)
        >>> a.ndim
        2
        >>> a.size
        7008

        >>> a.shape
        (1, 1, 1)
        >>> a.ndim
        3
        >>> a.size
        1

        >>> a.shape
        ()
        >>> a.ndim
        0
        >>> a.size
        1

        """
        return self._get_component("shape")

    @property
    def size(self):
        """Number of elements in the array.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.shape
        (73, 96)
        >>> a.size
        7008
        >>> a.ndim
        2

        >>> a.shape
        (1, 1, 1)
        >>> a.ndim
        3
        >>> a.size
        1

        >>> a.shape
        ()
        >>> a.ndim
        0
        >>> a.size
        1

        """
        return self._get_component("size")

    def get_filename(self):
        """The name of the netCDF file containing the array.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.get_filename()
        'file.nc'

        """
        return self._get_component("filename")

    def get_group(self):
        """The netCDF4 group structure of the netCDF variable.

        .. versionadded:: (cfdm) 1.8.6.0

        **Examples:**

        >>> b = a.get_group()

        """
        return self._get_component("group")

    def get_mask(self):
        """The mask of the data array.

        .. versionadded:: (cfdm) 1.8.2

        **Examples:**

        >>> b = a.get_mask()

        """
        return self._get_component("mask")

    def get_ncvar(self):
        """The name of the netCDF variable containing the array.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> print(a.netcdf)
        'tas'
        >>> print(a.varid)
        None

        >>> print(a.netcdf)
        None
        >>> print(a.varid)
        4

        """
        return self._get_component("ncvar")

    def get_varid(self):
        """The UNIDATA netCDF interface ID of the array's variable.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> print(a.netcdf)
        'tas'
        >>> print(a.varid)
        None

        >>> print(a.netcdf)
        None
        >>> print(a.varid)
        4

        """
        return self._get_component("varid")

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def close(self):
        """Close the `netCDF4.Dataset` for the file containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `None`

        **Examples:**

        >>> a.close()

        """
        netcdf = self._get_component("netcdf")
        if netcdf is None:
            return

        netcdf.close()
        self._set_component("netcdf", None, copy=False)

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples:**

        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    def open(self):
        """Returns an open `netCDF4.Dataset` for the array's file.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `netCDF4.Dataset`

        **Examples:**

        >>> netcdf = a.open()
        >>> variable = netcdf.variables[a.get_ncvar()]
        >>> variable.getncattr('standard_name')
        'eastward_wind'

        """
        if self._get_component("netcdf") is None:
            try:
                netcdf = netCDF4.Dataset(self.get_filename(), "r")
            except RuntimeError as error:
                raise RuntimeError(f"{error}: {self.get_filename()}")

            self._set_component("netcdf", netcdf, copy=False)

        return netcdf

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The array that is stored in memory.

        **Examples:**

        >>> b = a.to_memory()

        """
        return NumpyArray(self[...])
