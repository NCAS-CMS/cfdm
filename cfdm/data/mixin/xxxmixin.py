import netCDF4
import numpy as np

class XXXMixin:
    """Mixin class TODOHDF

    .. versionadded:: (cfdm) HDFVER

    """

    def _process_string_and_char(self, array):
        """TODOHDF"""
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
