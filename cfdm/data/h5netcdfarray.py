import logging

import h5netcdf
import netCDF4

from . import abstract
from .mixin import FileArrayMixin, NetCDFFileMixin
from .variableindexer import VariableIndexer

_safecast = netCDF4.utils._safecast
default_fillvals = netCDF4.default_fillvals.copy()
default_fillvals["O"] = default_fillvals["S1"]

logger = logging.getLogger(__name__)


class H5netcdfArray(NetCDFFileMixin, FileArrayMixin, abstract.Array):
    """An underlying array stored in a netCDF HDF file.

    .. versionadded:: (cfdm) HDFVER

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
        s3=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of) `str`, optional
                The name of the file(s) containing the array.

            address: (sequence of) `str`, optional
                The identity of the variable in each file defined by
                *filename*. Must be a netCDF variable name.

            dtype: `numpy.dtype`
                The data type of the array in the file. May be `None`
                if the numpy data-type is not known (which can be the
                case for string types, for example).

            shape: `tuple`
                The array dimension sizes in the file.

            size: `int`
                Number of elements in the array in the file.

            ndim: `int`
                The number of array dimensions in the file.

            mask: `bool`
                If True (the default) then mask by convention when
                reading data from disk.

                A netCDF array is masked depending on the values of any of
                the netCDF variable attributes ``valid_min``,
                ``valid_max``, ``valid_range``, ``_FillValue`` and
                ``missing_value``.

            units: `str` or `None`, optional
                The units of the variable. Set to `None` to indicate
                that there are no units. If unset then the units will
                be set during the first `__getitem__` call.

            calendar: `str` or `None`, optional
                The calendar of the variable. By default, or if set to
                `None`, then the CF default calendar is assumed, if
                applicable. If unset then the calendar will be set
                during the first `__getitem__` call.

            missing_values: `dict`, optional
                The missing value indicators defined by the variable
                attributes. See `get_missing_values` for details.

            s3: `dict` or `None`, optional
                The `s3fs.S3FileSystem` options for accessing S3
                files. If there are no options then ``anon=True`` is
                assumed, and if there is no ``'endpoint_url'`` key
                then one will automatically be derived one for each S3
                filename.

                .. versionadded:: (cfdm) HDFVER

            {{init source: optional}}

            {{init copy: `bool`, optional}}

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

            try:
                s3 = source._get_component("s3", None)
            except AttributeError:
                s3 = None

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
        self._set_component("s3", s3, copy=False)

        # By default, close the file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        .. versionadded:: (cfdm) HDFVER

        """
        dataset, address = self.open()
        dataset0 = dataset

        mask = self.get_mask()
        groups, address = self.get_groups(address)

        if groups:
            dataset = self._group(dataset, groups)

        # Get the variable by netCDF name
        variable = dataset.variables[address]

        # Get the data, applying masking and scaling as required.
        array = VariableIndexer(
            variable, mask=mask, scale=mask, always_masked=False
        )
        array = array[indices]

        # Set the units, if they haven't been set already.
        self._set_units(variable)

        self.close(dataset0)
        del dataset, dataset0

        return array

    def _get_attr(self, var, attr):
        """Get a variable attribute.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

            var: `h5netcdf.Variable`
                The variable.

            attr: `str`
                The attribute name.

        :Returns:

            The attirbute value.

        """
        return var.attrs[attr]

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

            dataset: `h5netcdf.File`
                The netCDF dataset to be be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

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

    def open(self, **kwargs):
        """Return a dataset file object and address.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and a file object is
        returned from the first file that exists.

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(
            h5netcdf.File, mode="r", decode_vlen_strings=True, **kwargs
        )
