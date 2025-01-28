import netCDF4

from . import abstract
from .locks import netcdf_lock
from .mixin import FileArrayMixin, IndexMixin, NetCDFFileMixin
from .netcdfindexer import netcdf_indexer


class NetCDF4Array(
    IndexMixin, NetCDFFileMixin, FileArrayMixin, abstract.Array
):
    """A netCDF array accessed with `netCDF4`.

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

                .. versionadded:: (cfdm) 1.11.2.0

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from the netCDF variable during
                the first `__getitem__` call.

                .. versionadded:: (cfdm) 1.11.2.0

            {{init storage_options: `dict` or `None`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

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

            units: `str` or `None`, optional
                Deprecated at version 1.11.2.0. Use the
                *attributes* parameter instead.

            calendar: `str` or `None`, optional
                Deprecated at version 1.11.2.0. Use the
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

    def __dask_tokenize__(self):
        """Return a value fully representative of the object.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return super().__dask_tokenize__() + (self.get_mask(),)

    @property
    def _lock(self):
        """Return the lock used for netCDF file access.

        Returns a lock object that prevents concurrent reads of netCDF
        files, which are not currently supported by `netCDF4`.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return netcdf_lock

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The subspace is defined by the `index` attributes, and is
        applied with `cfdm.netcdf_indexer`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()

        # Note: We need to lock because netCDF-C is about to access
        #       the file.
        with self._lock:
            netcdf, address = self.open()
            dataset = netcdf

            groups, address = self.get_groups(address)
            if groups:
                # Traverse the group structure, if there is one (CF>=1.8).
                netcdf = self._group(netcdf, groups)

            if isinstance(address, str):
                # Get the variable by netCDF name
                variable = netcdf.variables[address]
            else:
                # Get the variable by netCDF integer ID
                for variable in netcdf.variables.values():
                    if variable._varid == address:
                        break

            # Get the data, applying masking and scaling as required.
            array = netcdf_indexer(
                variable,
                mask=self.get_mask(),
                unpack=self.get_unpack(),
                always_masked_array=False,
                orthogonal_indexing=True,
                copy=False,
            )
            array = array[index]

            # Set the attributes, if they haven't been set already.
            self._set_attributes(variable)

            self.close(dataset)
            del netcdf, dataset

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1, 1d
            array = array.squeeze()

        return array

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during `{{class}}`
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var: `netCDF4.Variable`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes.

        """
        attributes = self._get_component("attributes", None)
        if attributes is not None:
            return

        attributes = {attr: var.getncattr(attr) for attr in var.ncattrs()}
        self._set_component("attributes", attributes, copy=False)

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

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dataset: `netCDF4.Dataset`
                The netCDF dataset to be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def open(self):
        """Return a dataset file object and address.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and a file object is
        returned from the first file that exists.

        :Returns:

            (`netCDF4.Dataset`, `str`)
                The file object open in read-only mode, and the
                address of the data within the file.

        """
        return super().open(netCDF4.Dataset, mode="r")
