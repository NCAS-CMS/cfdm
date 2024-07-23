import logging

import h5netcdf
import netCDF4

from . import abstract
from .mixin import FileArrayMixin, NetCDFFileMixin
from .netcdfindexer import netcdf_indexer

_safecast = netCDF4.utils._safecast
default_fillvals = netCDF4.default_fillvals.copy()
default_fillvals["O"] = default_fillvals["S1"]

logger = logging.getLogger(__name__)


class H5netcdfArray(NetCDFFileMixin, FileArrayMixin, abstract.Array):
    """A netCDF array accessed with `h5netcdf`.

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

            {{init mask: `bool`, optional}}

            {{init unpack: `bool`, optional}}

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from the netCDF variable during
                the first `__getitem__` call.

                .. versionadded:: (cfdm) NEXTVERSION

            {{init storage_options: `dict` or `None`, optional}}

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

        # By default, close the file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        .. versionadded:: (cfdm) NEXTVERSION

        """
        dataset, address = self.open()
        dataset0 = dataset

        groups, address = self.get_groups(address)
        if groups:
            dataset = self._group(dataset, groups)

        # Get the variable by netCDF name
        variable = dataset.variables[address]

        # Get the data, applying masking and scaling as required.
        array = netcdf_indexer(
            variable,
            mask=self.get_mask(),
            unpack=self.get_unpack(),
            always_masked_array=False,
            orthogonal_indexing=True,
            copy=False,
        )
        array = array[indices]

        # Set the attributes, if they haven't been set already.
        self._set_attributes(variable)

        self.close(dataset0)
        del dataset, dataset0

        return array

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during `{{class}}`
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `h5netcdf.Variable`
                The netCDF variable.

        :Returns:

            `None`

        """
        if self._get_component("attributes", None) is not None:
            return

        self._set_component("attributes", dict(var.attrs), copy=False)

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `h5netcdf.File`
                The netCDF dataset to be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def get_groups(self, address):
        """The netCDF4 group structure of a netCDF variable.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            address: `str` or `int`
                The netCDF variable name, or integer varid, from which
                to get the groups.

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

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(
            h5netcdf.File, mode="r", decode_vlen_strings=True, **kwargs
        )
