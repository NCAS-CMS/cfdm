# from . import FileArray


class NetCDFFileArray:  # (FileArray):
    """Abstract base class for an array in a netCDF file.

    .. versionadded:: (cfdm) NEXTVERSION

    """


#    def __init__(
#        self,
#        filename=None,
#        address=None,
#        dtype=None,
#        shape=None,
#        mask=True,
#        unpack=True,
#        attributes=None,
#        storage_options=None,
#        source=None,
#        copy=True,
#    ):
#        super().__init__(
#            filename=filename,
#            address=address,
#            dtype=dtype,
#            shape=shape,
#            mask=mask, unpack=unpack,
#            storage_options=storage_options,
#            source=source,
#            copy=copy,
#        )
#
#        if source is not None:
##            try:
##                unpack = source._get_component("unpack", True)
##            except AttributeError:
##                unpack = True
#
#            try:
#                attributes = source._get_component("attributes", None)
#            except AttributeError:
#                attributes = None
#
##        self._set_component("unpack", bool(unpack), copy=False)
#        self._set_component("attributes", attributes, copy=False)
#
#    def __dask_tokenize__(self):
#        """Return a value fully representative of the object.##
#
#        .. versionadded:: (cfdm) NEXTVERSION
#
#        """
#       return super().__dask_tokenize__() + (self.get_unpack(),)
#
#    def _set_attributes(self, var):
#        """Set the netCDF variable attributes.
#
#        These are set from the netCDF variable attributes, but only if
#        they have not already been defined, either during {{class}}
#        instantiation or by a previous call to `_set_attributes`.
#
#        .. versionadded:: (cfdm) NEXTVERSION
#
#        :Parameters:
#
#            var: `netCDF4.Variable` or `h5netcdf.Variable`
#                The netCDF variable.
#
#        :Returns:
#
#            `dict`
#                The attributes.
#
#        """
#        raise NotImplementedError(
#            f"Must implement {self.__class__.__name__}._set_attributes"
#        )  # pragma: no cover

#    def get_format(self):
#        """The format of the files.
#
#        .. versionadded:: (cfdm) 1.10.1.0
#
#        .. seealso:: `get_address`, `get_filename`, `get_formats`
#
#        :Returns:
#
#            `str`
#                The file format. Always ``'nc'``, signifying netCDF.
#
#        **Examples**
#
#        >>> a.get_format()
#        'nc'
#
#        """
#        return "nc"

#    def get_unpack(self):
#        """Whether or not to automatically unpack the data.
#
#        .. versionadded:: (cfdm) NEXTVERSION
#
#        **Examples**
#
#        >>> a.get_unpack()
#        True
#
#        """
#        return self._get_component("unpack")
