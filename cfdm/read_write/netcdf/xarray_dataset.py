class XarrayDataset:
    """An `xarray.Dataset` constructor.

    Has a similar API to `netCDF4.Dataset`.

    If the `cf_xarray` package (https://cf-xarray.readthedocs.io) is
    installed then the `cf_xarray` accessors will be present on the
    returned `xarray` objects (`xarray.DataArray.cf` and
    `xarray.Dataset.cf`) that allow some interpretation of CF
    attributes.

    .. versionadded:: (cfdm) NEXVERSION

    """

    def __init__(self):
        """**Initialisation**"""
        try:
            import xarray as xr
        except ModuleNotFoundError as error:
            error.msg += (
                ". Install the 'xarray' package "
                "(https://pypi.org/project/xarray) to convert to a xarray "
                "datasets"
            )
            raise

        # Attempt to apply the cf_xarray accessors
        try:
            import cf_xarray  # noqa: F401
        except ModuleNotFoundError:
            pass
        else:
            # cf_xarray works best when xarray keeps attributes by
            # default.
            xr.set_options(keep_attrs=True)

        self.ds = xr.Dataset()
        self.attrs = self.ds.attrs
        self.coords = {}
        self.data_vars = {}

    def createDimension(self, *args, **kwargs):
        """Create a new dimension.

        Has a similar API to `netCDF4.createDimension`.

        `xarray` handles dimensions implicitly, so this method does
        nothing.

        .. versionadded:: (cfdm) NEXVERSION

        :Returns:

            `None`

        """
        pass

    def createVariable(self, name, datatype, dimensions=(), coordinate=False):
        """Create a new variable.

        Has a similar API to `netCDF4.createVariable`.

        .. versionadded:: (cfdm) NEXVERSION

        :Parameters:

            varname: `str`
                The name of the variable.

            datatype: data-type
                Typecode or data-type of the variable.

            dimensions: sequence of `str`, optional
                The dimension of the variable.

            coordinate: `bool`, optional
                If True then the variable represents coordinates (but
                not bounds). If False (the default), then it does not.

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
        """Return the `xarray.Dataset` instance.

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
    """An `xarray.DataAray` constructor.

    Has a similar API to `netCDF4.Variable`.

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
        """Return the `xarray.DataArray` instance.

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
