import netCDF4

from . import abstract
from .locks import netcdf_lock
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class NetCDF4Array(IndexMixin, abstract.FileArray):
    """A netCDF array accessed with `netCDF4`.

    .. versionadded:: (cfdm) 1.7.0

    """

    @property
    def _lock(self):
        """Set the lock for use in `dask.array.from_array`.

        Returns a lock object because concurrent reads are not
        currently supported by the netCDF and HDF libraries. The lock
        object will be the same for all `NetCDF4Array` and
        `H5netcdfArray` instances, regardless of the dataset they
        access, which means that access to all netCDF and HDF files
        coordinates around the same lock. TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return netcdf_lock

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        TODODASK

        The indices that define the subspace must be a sequence that
        contains an index for each dimension.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        .. versionadded:: NEXTVERSION

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()

        # Note: We need to lock because the netCDF file is about to be
        #       accessed.
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

        #       self._lock.release()
        return array

    def _group(self, dataset, groups):
        """Return the group object containing a variable.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `netCDF4.Dataset
                The dataset containing the variable.

            groups: sequence of `str`
                The definition of which group the variable is in. For
                instance, of the variable is in group
                ``/forecast/model`` then *groups* would be
                ``['forecast', 'model']``.

        :Returns:

            `netCDF4.Dataset` or `netCDF4.Group`
                The group object, which might be the root group.

        """
        for g in groups:
            dataset = dataset.groups[g]

        return dataset

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during `{{class}}`
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) NEXTVERSION

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
