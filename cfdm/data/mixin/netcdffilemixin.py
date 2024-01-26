import netCDF4
import numpy as np

from ..numpyarray import NumpyArray


class NetCDFFileMixin:
    """Mixin class TODOHDF.

    .. versionadded:: (cfdm) HDFVER

    """

    #    def __repr__(self):
    #        """Called by the `repr` built-in function.
    #
    #        x.__repr__() <==> repr(x)
    #
    #        """
    #        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def _get_attr(self, var, attr):
        """TODOHDF.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

        """
        raise NotImplementedError(
            "Must implement {self.__class__.__name__}._get_attr"
        )  # pragma: no cover

    @classmethod
    def _process_string_and_char(cls, array):
        """TODOHDF."""
        string_type = isinstance(array, str)
        kind = array.dtype.kind
        if not string_type and kind in "SU":
            # Collapse by concatenation the outermost (fastest
            # varying) dimension of char array into
            # memory. E.g. [['a','b','c']] becomes ['abc']
            if kind == "U":
                array = array.astype("S", copy=False)

            array = netCDF4.chartostring(array)
            shape = array.shape
            array = np.array([x.rstrip() for x in array.flat], dtype="U")
            array = np.reshape(array, shape)
            array = np.ma.masked_where(array == "", array)
        elif not string_type and kind == "O":
            # An N-d (N>=1) string variable comes out as a numpy
            # object array, so convert it to numpy string array.
            array = array.astype("U", copy=False)

            # Mask the VLEN variable
            array = np.ma.where(array == "", np.ma.masked, array)

        return array

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

    def _uuu(self, dataset, groups):
        for g in groups:  # [:-1]:
            dataset = dataset.groups[g]

        return dataset  # dataset = dataset.groups[groups[-1]]

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

    def get_s3(self):
        """Return `s3fs.S3FileSystem` options for accessing S3 files.

        .. versionadded:: (cfdm) HDFVER

        :Returns:

            `dict`
                The `s3fs.S3FileSystem` options for accessing S3
                files. If there are no options then ``anon=True`` is
                assumed, and if there is no ``'endpoint_url'`` key
                then one will automatically be derived one for each S3
                filename.

        """
        out = self._get_component("s3", None)
        if not out:
            return {}

        return out.copy()

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
