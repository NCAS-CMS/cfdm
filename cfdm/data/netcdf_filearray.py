from scipy.io import netcdf_file

from .abstract import FileArray
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class Netcdf_fileArray(IndexMixin, FileArray):
    """A netCDF-3 array accessed with `scipy.io.netcdf_file`.

    .. versionadded:: (cfdm) NEXTVERSION

    """

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

        dataset, address = self.open()
        variable = dataset.variables[address]

        # Get the data, applying masking and scaling as required.
        array = netcdf_indexer(
            variable,
            mask=self.get_mask(),
            unpack=self.get_unpack(),
            always_masked_array=False,
            orthogonal_indexing=True,
            attributes=self._set_attributes(variable),
            copy=False,
        )
        array = array[index]

        # Must copy the array to allow the dataset to be closed:
        # https://scipy.github.io/devdocs/reference/generated/scipy.io.netcdf_file.html
        array = array.copy()

        self.close(dataset)
        del dataset, variable

        return array

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during `{{class}}`
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `scipy.io.netcdf_variable`
                The netCDF-3 variable.

        :Returns:

            `dict`
                The attributes.

        """
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = var._attributes
            self._set_component("attributes", attributes, copy=False)
            
        return attributes

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
        return super().open(necdf_file, mode="r", mmap=True)
