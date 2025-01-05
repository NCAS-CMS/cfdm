from .abstract import FileArray
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer


class VariableArray(IndexMixin, FileArray):
    """A netCDF array accessed with `???`. TODOVAR

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

        # Get the variable for subspacing
        variable =  self.get_variable()
        if variable is None:
            dataset, address = self.open()            
            dataset0 = dataset
            
            groups, address = self.get_groups(address)
            if groups:
                dataset = self._group(dataset, groups)

            variable = dataset.variables[address]

            # Cache the variable
            self._set_variable(variable)

            self.close(dataset0)
            del dataset, dataset0
                    
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

    def _set_attributes(self, var):
        """Set the netCDF variable attributes. TODOVAR

        These are set from the netCDF TODOVAR variable attributes, but
        only if they have not already been defined, either during
        `{{class}}` instantiation or by a previous call to
        `_set_attributes`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `netCDF4.Variable` TODOVAR
                The netCDF variable. TODOVAR

        :Returns:

            `dict`
                The attributes.

        """
        # TODOVAR ; modify for 'Variable' API
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = {attr: var.getncattr(attr) for attr in var.ncattrs()}
            self._set_component("attributes", attributes, copy=False)
            
        return attributes

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

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(
            h5netcdf.File, mode="r", decode_vlen_strings=True, **kwargs
        )
