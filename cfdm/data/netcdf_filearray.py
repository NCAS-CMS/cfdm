from scipy.io import netcdf_file

from .abstract import FileArray
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class Netcdf_fileArray(IndexMixin, FileArray):
    """A netCDF-3 array accessed with `scipy.io.netcdf_file`.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def _attributes(self, var):
        """Get the netCDF variable attributes.

        If the attributes have not been set, then they are retrieved
        from the netCDF variable *var* and stored in `{{class}}`
        instance for fast future access.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `scipy.io.netcdf_variable`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes. The returned attributes are not a copy
                of the cached dictionary.

        """
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = var._attributes
            self._set_component("attributes", attributes, copy=False)

        return attributes

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()
        #        print(self.__class__.__name__, "_get_array", index)

        dataset, address = self.open()
        variable = dataset.variables[address]

        # Get the data, applying masking and scaling as required.
        array = netcdf_indexer(
            variable,
            mask=self.get_mask(),
            unpack=self.get_unpack(),
            always_masked_array=False,
            orthogonal_indexing=True,
            attributes=self._attributes(variable),
            copy=False,
        )
        array = array[index]

        # Close the dataset.
        #
        # Before 'dataset' can be closed we must:
        #
        # * Replace 'array' (which is currently a memory map view of
        #   the data on disk) with a copy of itself.
        # * Delete references to 'variable'.
        #
        # For reasons why, see the docs for `scipy.io.netcdf_file`.
        array = array.copy()
        del variable
        self.close(dataset)

        return array

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `scipy.io.netcdf_file`
                The dataset to be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def open(self):
        """Return a dataset file object and address.

        :Returns:

            (`scipy.io.netcdf_file`, `str`)
                The file object open in read-only mode, and the
                address of the data within the file.

        """
        return super().open(netcdf_file, mode="r", mmap=True)
