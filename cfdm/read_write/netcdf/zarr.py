class ZarrDimension:
    """A named Zarr dimension.

    This class defines a Zarr dimension with the same API as
    `netCDF4.Dimension`.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def __init__(self, name, size, group, reference_variable=None):
        """**Initialisation**

        :Parameters:

            name: `str`
                The dimension name.

            size: `int`
                The dimension size.

            group: `zarr.Group`
                The group that the dimension is a member of.

            reference_variable: `zarr.Array`, optional
                The variable that provided the dimension definition.

                .. versionadded:: (cfdm) NEXTVERSION

        """
        self._name = name
        self._size = size
        self._group = group
        self._reference_variable = reference_variable

    def __len__(self):
        """The size of the dimension.

        x.__len__() <==> len(x)

        .. versionadded:: (cfdm) 1.12.2.0

        """
        return self.size

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.12.2.0

        """
        return f"<ZarrDimension {self.name!r}, size {self.size}>"

    @property
    def name(self):
        """Return the dimension name.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self._name

    @property
    def size(self):
        """Return the dimension size.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self._size

    def group(self):
        """Return the group that the dimension is a member of.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `zarr.Group`
                The group containing the dimension.

        """
        return self._group

    def isunlimited(self):
        """Whether or not the dimension is unlimited.

        In Zarr v2 and v3, dimensions can not be unlimited.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `bool`
                `True` if and only if the dimension is unlimited.

        """
        return False

    def reference_variable(self):
        """Return the variable that provided the dimension definition.

        Note that the variable does not have to be in the dimension's
        `group`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `zarr.Array` or `None`
                The variable that provided the dimension definition,
                or `None` if it wasn't provided during instance
                initialisation.

        """
        return self._reference_variable
