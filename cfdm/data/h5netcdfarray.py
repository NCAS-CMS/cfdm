import logging

import h5netcdf

from . import abstract
from .locks import netcdf_lock
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer

logger = logging.getLogger(__name__)


class H5netcdfArray(IndexMixin, abstract.FileArray):
    """A netCDF array accessed with `h5netcdf`.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    @property
    def _lock(self):
        """Return the lock used for netCDF file access.

        Returns a lock object that prevents concurrent reads of netCDF
        files, which are not currently supported by `h5netcdf`.

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

        # Note: We need to lock because HDF5 is about to access the
        #       file.
        with self._lock:
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
            array = array[index]

            # Set the attributes, if they haven't been set already.
            self._set_attributes(variable)

            self.close(dataset0)
            del dataset, dataset0

        return array

    def _group(self, dataset, groups):
        """Return the group object containing a variable.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            dataset: `h5netcdf.File`
                The dataset containing the variable.

            groups: sequence of `str`
                The definition of which group the variable is in. For
                instance, if the variable is in group
                ``/forecast/model`` then *groups* would be
                ``['forecast', 'model']``.

        :Returns:

            `h5netcdf.File` or `h5netcdf.Group`
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

        .. versionadded:: (cfdm) 1.11.2.0

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

        .. versionadded:: (cfdm) 1.11.2.0

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

        .. versionadded:: (cfdm) 1.11.2.0

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

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(
            h5netcdf.File, mode="r", decode_vlen_strings=True, **kwargs
        )
