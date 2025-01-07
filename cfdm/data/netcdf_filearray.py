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

        If the attributes haven't been set then they are retrived from
        *variable* and stored for future use. This differs from
        `get_attributes`, which will return an empty dictionary if the
        attributes haven't been set.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_attributes`

        :Parameters:

            var: `scipy.io.netcdf_variable`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes.

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
        print(self.__class__.__name__, "_get_array", index)

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

        # So that the dataset can be closed:
        #
        # 1. Must copy the array
        # 2. Must delete the variable
        #
        # This is because the dataset was opened in `open` with
        # 'mmap=True'. See the scipy.io.netcdf_file docstring for more
        # information.
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
