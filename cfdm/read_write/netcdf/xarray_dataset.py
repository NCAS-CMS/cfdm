class XarrayDataset:
    """An `xarray` dataset` constructor.

    Constructs either `xarray.Dataset` (if there are no sub-groups of
    the root group) or else `xarray.DataTree` (if there are sub-groups
    of the root group).

    If the `cf_xarray` package (https://cf-xarray.readthedocs.io) is
    installed then the `cf_xarray` accessors that allow some
    interpretation of CF attributes will be present on
    `xarray.DataArray` and `xarray.Dataset` objects.

    Has a similar API to `netCDF4.Dataset`.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(self, name=None):
        """**Initialisation**

        :Parameters:

            name: `str` or `None`
                The name of the group, or `None` for the root group.

        """
        try:
            import xarray as xr
        except ModuleNotFoundError as error:
            error.msg += (
                ". Install the 'xarray' package "
                "(https://pypi.org/project/xarray) to convert to an xarray "
                "dataset"
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
        self.name = name
        self.attrs = self.ds.attrs
        self.coords = {}
        self.data_vars = {}

        # XarrayDataset objects in sub-groups
        self.groups = {}

    def createDimension(self, *args, **kwargs):
        """Create a new dimension.

        Has a similar API to `netCDF4.createDimension`.

        `xarray` handles dimensions implicitly, so this method does
        nothing.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        pass

    def createGroup(self, group_name):
        """Creates a new group with the given group name.

        Has a similar API to `netCDF4.createGroup`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group_name: `str`
                The name of the group. Th group is created directly
                inside the calling parent group, and *group_name*
                can't contain ``/``.

        :Returns:

            `XarrayDataset`

        """
        if "/" in group_name:
            raise ValueError(
                f"Cant create group {group_name!r}: Can only create "
                "subgroups directly inside the parent"
            )

        new_group = type(self)(name=group_name)
        self.groups[group_name] = new_group

        return new_group

    def createVariable(self, name, datatype, dimensions=(), coordinate=False):
        """Create a new variable.

        Has a similar API to `netCDF4.createVariable`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            varname: `str`
                The name of the variable. May contain a group
                structure defined by ``/`` characters.

            datatype: data-type
                Typecode or data-type of the variable.

            dimensions: sequence of `str`, optional
                The dimension of the variable.

            coordinate: `bool`, optional
                If True then the variable represents coordinates (but
                not bounds). If False (the default), then it does not.

        :Returns:

            `XarrayVariable`

        """
        # Get the group in which to create the variable
        g = self
        if "/" in name:
            parts = name.split("/")
            for group_name in parts[:-1]:
                if not group_name:
                    continue

                if group_name in g.groups:
                    # Use existing group
                    g = g.groups[group_name]
                else:
                    # Create a new group
                    g = g.createGroup(group_name)

            # Remove the group structure from the variable name
            name = parts[-1]

        # Create the variable
        var = XarrayVariable(
            name=name,
            datatype=datatype,
            dimensions=dimensions,
        )

        if coordinate:
            g.coords[name] = var
        else:
            g.data_vars[name] = var

        return var

    def setncatts(self, attributes):
        """Set dataset attributes.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        self.ds.attrs.update(attributes)

    def to_xarray(self):
        """Return the `xarray` dataset.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `xarray.Dataset` or `xarray.DataTree`

        """
        ds = self.ds

        for name, var in self.coords.items():
            ds.coords[name] = var.to_xarray()

        for name, var in self.data_vars.items():
            ds[name] = var.to_xarray()

        if not self.groups:
            # --------------------------------------------------------
            # Return an xr.Dataset that has no group structure
            # --------------------------------------------------------
            return ds

        # ------------------------------------------------------------
        # Return an xr.DataTree that has a group structure
        # ------------------------------------------------------------
        import xarray as xr

        current_group = xr.DataTree(dataset=ds, name=self.name)

        # Recursively convert children to xarray, and attach them.
        for parent_group_name, parent_group in self.groups.items():
            child_group = parent_group.to_xarray()

            if isinstance(child_group, xr.Dataset):
                # Create a node for the Dataset
                child_node = xr.DataTree(
                    dataset=child_group, name=parent_group_name
                )
            else:
                # child_output is already a DataTree node
                child_node = child_group
                child_node.name = parent_group_name

            # Use the node itself as a dictionary. This is the
            # xr.DataTree way to add a child.
            current_group[parent_group_name] = child_node

        return current_group


class XarrayVariable:
    """An `xarray.DataArray` constructor.

    Has a similar API to `netCDF4.Variable`.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(self, name, datatype, dimensions=()):
        """**Initialisation**

        :Parameters:

            name: `str`
                The name of the variable.

            datatype: data-type
                Typecode or data-type of the variable.

            dimensions: sequence of `str`, optional
                The names of the dimensions of the variable.

        """
        self.name = name
        self.datatype = datatype
        self.dimensions = dimensions
        self.attrs = {}

    def setncatts(self, attributes):
        """Set variable attributes.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        self.attrs.update(attributes)

    def to_xarray(self):
        """Return the `xarray` variable.

        .. versionadded:: (cfdm) NEXTVERSION

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
