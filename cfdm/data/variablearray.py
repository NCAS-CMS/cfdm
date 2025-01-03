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

        variable, _ = self.open()

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

        self.close(variable)

        return array

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
        # TODOVAR
        pass

    def open(self):
        """Return a dataset file object and address.

        :Returns:

            (`netCDF4.Dataset`, `str`) TODOVAR
                The file object open in read-only mode, and the
                address of the data within the file.

        """
        variable =  getattr(self, '_variable', None)
        if variable is not None:
            return variable, self.get_address()
        
        variable, address =  super().open(Variable, mode="r") # TODOVAR
        self._variable = variable
        return variable, address

    def replace_directory(self, old=None, new=None, normalise=False):
        """Replace the file directory.

        Modifies the name of the file.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `file_directory`, `get_filename`

        :Parameters:

            old: `str` or `None`, optional
                The base directory structure to be replaced by
                *new*. If `None` (the default) or an empty string, and
                *normalise* is False, then *new* is prepended to each
                file name.

            new: `str` or `None`, optional
                The new directory that replaces the base directory
                structure identified by *old*. If `None` (the default)
                or an empty string, then *old* is replaced with an
                empty string. Otherwise,

            normalise: `bool`, optional
                If True then *old*, *new*, and the file name are
                normalised to absolute paths prior to the
                replacement. If False (the default) then no
                normalisation is done.

        :Returns:

            `{{class}}`
                A new `{{class}}` with modified file locations.

        **Examples**

        >>> a.get_filename()
        '/data/file1.nc'
        >>> b = a.replace_directory('/data', '/new/data/path/')
        >>> b.get_filename()
        '/new/data/path/file1.nc'
        >>> c = b.replace_directory('/new/data', None)
        >>> c.get_filename()
        'path/file1.nc'
        >>> c = b.replace_directory('path', '../new_path', normalise=False)
        >>> c.get_filename()
        '../new_path/file1.nc'
        >>> c = b.replace_directory(None, '/data')
        >>> c.get_filename()
        '/data/../new_path/file1.nc'
        >>> c = b.replace_directory('/new_path/', None, normalise=True)
        >>> c.get_filename()
        'file1.nc'

        """
        a = super().replace_directory(old=old, new=new, normalise=normalise)
        a._variable = None
        return a

    def replace_filename(self, filename):
        """Replace the file location.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `file_directory`, `get_filename`,
                     `replace_directory`

        :Parameters:

            filename: `str`
                The new file location.

        :Returns:

            `{{class}}`
                A new `{{class}}` with modified file name.

        """
        a = super().replace_directory(filename)
        a._variable = None
        return a
