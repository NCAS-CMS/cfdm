class ZarrDimension:
    """A named Zarr dimension.

    This class defines a Zarr dimension with the same API as
    `netCDF4.Dimension`.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def __init__(self, name, size, group):
        """**Initialisation**

        :Parameters:

            name: `str`
                The dimension name.

            size: `int`
                The dimension size.

            group: `zarr.Group`
                The group that the dimension is a member of.

        """
        self.name = name
        self.size = size
        self.group = group

    def __len__(self):
        """The size of the dimension.

        x.__len__() <==> len(x)

        .. versionadded:: (cfdm) 1.12.2.0

        """
        return self.size

    def group(self):
        """Return the group that the dimension is a member of.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `zarr.Group`
                The group containing the dimension.

        """
        return self.group

    def isunlimited(self):
        """Whether or not the dimension is unlimited.

        In Zarr v2 and v3, dimensions can not be unlimited.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `bool`
                `True` if and only if the dimension is unlimited.

        """
        return False
