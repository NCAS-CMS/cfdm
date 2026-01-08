from .abstract import FileArray
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class PyfiveArray(IndexMixin, FileArray):
    """A netCDF array accessed with `pyfive`.

    * Accesses local and remote (http and s3) netCDF-4 datasets.
    * Allows parallised reading.
    * Improves the performance of active storage reductions (by
      storing the dataset variable's B-tree at read time so that it
      doesn't have to be re-retrieved at compute time).

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def _attributes(self, var):
        """Get the netCDF variable attributes.

        If the attributes have not been set, then they are retrieved
        from the netCDF variable *var* and stored in for fast future
        access.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `pyfive.Dataset`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes. The returned attributes are not a copy
                of the cached dictionary.

        """
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = dict(var.attrs)
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

        # Get the variable for subspacing
        variable = self.get_variable(None)

        dataset = None
        if variable is None:
            # The variable has not been provided, so get it.
            dataset, address = self.open()
            dataset0 = dataset

            groups, address = self.get_groups(address)
            if groups:
                dataset = self._group(dataset, groups)

            variable = dataset.variables[address]

            # Cache the variable
            self._set_component("variable", variable, copy=False)

            self.close(dataset0)
            del dataset, dataset0

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

        if dataset is not None:
            self.close(dataset0)

        return array

    def _group(self, dataset, groups):
        """Return the group object containing a variable.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `h5netcdf.File`
                The dataset containing the variable.

            groups: sequence of `str`
                The definition of which group the variable is in. For
                instance, of the variable is in group
                ``/forecast/model`` then *groups* would be
                ``['forecast', 'model']``.

        :Returns:

            `h5netcdf.File` or `h5netcdf.Group`
                The group object, which might be the root group.

        """
        for g in groups:
            dataset = dataset.groups[g]

        return dataset

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) NEXTVERSION

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

        :Parameters:

            kwargs: optional
                Extra keyword arguments to `h5netcdf.File`.

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        import h5netcdf

        return super().open(
            h5netcdf.File,
            mode="r",
            decode_vlen_strings=True,
            netcdf_backend="pyfive",
            phony_dims="sort",
            #            phony_dims='access'
            **kwargs
        )
