class BoundsMixin:
    """Mixin class for a bounds variable.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def __initialise_from_source(self, source, copy=True):
        """Initialise inherited properties from a source.

        This method is called by
        `_Container__parent_initialise_from_source`, which in turn is
        called by `cfdm.core.Container.__init__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            source:
                The object from which to extract the initialisation
                information. Typically, but not necessarily, a
                `{{class}}` object.

            copy: `bool`, optional
                If True (the default) then deep copy the
                initialisation information.

        :Returns:

            `None`

        """
        try:
            inherited_properties = source.inherited_properties()
        except AttributeError:
            inherited_properties = {}

        self._set_component(
            "inherited_properties", inherited_properties, copy=False
        )
