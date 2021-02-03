from . import PropertiesDataBounds


class Coordinate(PropertiesDataBounds):
    """Mixin class for dimension or auxiliary coordinate constructs.

    .. versionadded:: (cfdm) 1.7.0

    """

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="c",
        data_name="data",
        bounds_name="b",
        interior_ring_name="i",
        header=True,
    ):
        """Return the commands that would create the construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Data.creation_commands`,
                     `{{package}}.Field.creation_commands`

        :Parameters:

            {{representative_data: `bool`, optional}}

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{data_name: `str`, optional}}

            bounds_name: `str`, optional
                The name of the construct's `Bounds` instance created
                by the returned commands.

                *Parameter example:*
                  ``name='bounds1'``

            interior_ring_name: `str`, optional
                The name of the construct's `InteriorRing` instance
                created by the returned commands.

                *Parameter example:*
                  ``name='ir1'``

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples:**

        >>> x = {{package}}.{{class}}(
        ...     properties={'units': 'degrees_east',
        ...                 'standard_name': 'longitude'}
        ... )
        >>> x.set_data([22.5, 67.5, 112.5])
        >>> b = {{package}}.Bounds()
        >>> b.set_data([[0.0, 45.0], [45.0, 90.0], [90.0, 135.0]])
        >>> x.set_bounds(b)
        >>> print(x.creation_commands(header=False))
        c = {{package}}.{{class}}()
        c.set_properties({'units': 'degrees_east', 'standard_name': 'longitude'})
        data = {{package}}.Data([22.5, 67.5, 112.5], units='degrees_east', dtype='f8')
        c.set_data(data)
        b = {{package}}.Bounds()
        data = {{package}}.Data([[0.0, 45.0], [45.0, 90.0], [90.0, 135.0]], units='degrees_east', dtype='f8')
        b.set_data(data)
        c.set_bounds(b)

        """
        return super().creation_commands(
            representative_data=representative_data,
            namespace=namespace,
            indent=0,
            string=string,
            name="c",
            data_name="data",
            bounds_name="b",
            interior_ring_name="i",
            header=header,
            _coordinate=True,
        )
