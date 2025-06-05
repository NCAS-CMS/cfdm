from . import abstract
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class ZarrArray(IndexMixin, abstract.FileArray):
    """A Zarr array accessed with `zarr`.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()

        zr, address = self.open()

        # Get the variable by name
        variable = zr[address]

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

        self.close(zr)

        return array

    def _set_attributes(self, var):
        """Set the Zarr variable attributes.

        These are set from the Zarr variable attributes, but only if
        they have not already been defined, either during `{{class}}`
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            var: `zarr.Array`
                The Zarr variable.

        :Returns:

            `dict`
                The attributes.

        """
        attributes = self._get_component("attributes", None)
        if attributes is not None:
            return

        self._set_component("attributes", dict(var.attrs), copy=False)

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            dataset:
                The dataset to be closed.

        :Returns:

            `None`

        """
        # `zarr.Group` objects don't need closing
        pass

    def open(self):
        """Return a dataset file object and address.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            (`zarr.Group`, `str`)
                The dataset object open in read-only mode, and the
                variable name of the data within the dataset.

        """
        import zarr

        return super().open(zarr.open, mode="r")
