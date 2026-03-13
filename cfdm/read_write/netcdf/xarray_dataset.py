class XarrayDataset:
    """A mimic of `netCDF4.Dataset` for `xarray.Dataset`.

    .. versionadded:: (cfdm) NEXVERSION

    """

    def __init__(self):
        """**Initialisation**"""
        import xarray as xr

        try:
            import cf_xarray  # noqa: F401
        except ModuleNotFoundError:
            raise
        else:
            # cf_xarray works best when xarray keeps attributes by
            # default.
            xr.set_options(keep_attrs=True)

        self.ds = xr.Dataset()
        self.attrs = self.ds.attrs
        self.coords = {}
        self.data_vars = {}

    def createDimension(self, **kwargs):
        """Create a new dimension.

        `xarray` handles dimensions implicitly, so this method does
        nothing.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `None`

        """
        pass

    def createVariable(self, name, datatype, dimensions=(), coordinate=False):
        """Create a new variable.

        .. versionadded:: (cfdm) NEXVERSION

        :Parameters:

            varname: `str`
                The name of the variable.

            datatype: data-type
                Typecode or data-type of the variable.

            dimensions: sequence of `str`, optional
                The dimension of the variable.

            coordinate: `bool`, optional
                If True then the variable represents a dimension or
                auxiliary coordinate construct. If False (the
                default), then it does not.

        :Returns:

            `None`

        """
        var = XarrayVariable(
            name=name,
            datatype=datatype,
            dimensions=dimensions,
        )

        if coordinate:
            self.coords[name] = var
        else:
            self.data_vars[name] = var

        return var

    def setncatts(self, attributes):
        """Set dataset attributes.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `None`

        """
        self.ds.attrs.update(attributes)

    def finalise(self):
        """Return the equivalent `xarray.Dataset`.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `xarray.Dataset`

        """
        for name, var in self.coords.items():
            self.ds.coords[name] = var.finalise()

        for name, var in self.data_vars.items():
            self.ds[name] = var.finalise()

        return self.ds


class XarrayVariable:
    """A mimic of `netCDF4.Variable` for `xarray.DataArray`.

    .. versionadded:: (cfdm) NEXVERSION

    """

    def __init__(self, name, datatype, dimensions=()):
        """**Initialisation**

        :Parameters:

            name: `str`
                The name of the variable.

            datatype: data-type
                Typecode or data-type of the variable.

            dimensions: sequence of `str`, optional
                The dimension of the variable.

        """
        self.name = name
        self.datatype = datatype
        self.dimensions = dimensions
        self.attrs = {}

    def setncatts(self, attributes):
        """Set variable attributes.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `None`

        """
        self.attrs.update(attributes)

    def finalise(self):
        """Return the equivalent `xarray.DataArray`.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `xarray.DataArray`

        """
        import xarray as xr

        if not hasattr(self, "data") and not self.dimensions:
            import numpy as np

            self.data = np.ma.masked_all((), dtype=self.datatype)

        data = getattr(self, "data", None)
        if data is None:
            raise ValueError(
                "Must set 'XarrayVariable.data' to return an xr.DataArray"
            )

        return xr.DataArray(
            data=data, dims=self.dimensions, name=self.name, attrs=self.attrs
        )
