class Dimension:
    """A named dimension.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(self, name, size, group):
        """**Initialisation**

        :Parameters:

            name: `str`
                The dimension name.

            size: `int`
                The dimension size.

            group:
                The group that the dimension is a member of.

        """
        self.name = name
        self.size = size
        self.group = group

    def __len__(self):
        """The size of the dimension.

        x.__len__() <==> len(x)

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.size

    def group(self):
        """Return the group that the dimension is a member of.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

                The group containing the dimension.

        """
        return self.group

    def isunlimited(self):
        """Whether or not the dimension is unlimited.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `bool`
                `True` if and only if the dimension is unlimited.

        """
        return False
