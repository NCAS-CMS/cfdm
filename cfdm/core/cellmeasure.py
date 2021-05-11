from . import abstract


class CellMeasure(abstract.PropertiesData):
    """A cell measure construct of the CF data model.

    A cell measure construct provides information that is needed about
    the size or shape of the cells and that depends on a subset of the
    domain axis constructs. Cell measure constructs have to be used
    when the size or shape of the cells cannot be deduced from the
    dimension or auxiliary coordinate constructs without special
    knowledge that a generic application cannot be expected to have.

    The cell measure construct consists of a numeric array of the
    metric data which spans a subset of the domain axis constructs,
    and properties to describe the data. The cell measure construct
    specifies a "measure" to indicate which metric of the space it
    supplies, e.g. cell horizontal areas, and must have a units
    property consistent with the measure, e.g. square metres. It is
    assumed that the metric does not depend on axes of the domain
    which are not spanned by the array, along which the values are
    implicitly propagated. CF-netCDF cell measure variables correspond
    to cell measure constructs.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        measure=None,
        properties=None,
        data=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            measure: `str`, optional
                Set the measure that indicates which metric given by
                the data array. Ignored if the *source* parameter is
                set.

                The measure may also be set after initialisation with
                the `set_measure` method.

                *Parameter example:*
                  ``measure='area'``

            {{init properties: `dict`, optional}}

                *Parameter example:*
                  ``properties={'units': 'metres 2'}``

            {{init data: data_like, optional}}

            source: optional
                Initialise the measure, properties and data from those
                of source.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            properties=properties,
            source=source,
            data=data,
            copy=copy,
            _use_data=_use_data,
        )

        if source is not None:
            try:
                measure = source.get_measure(None)
            except AttributeError:
                measure = None

        if measure is not None:
            self.set_measure(measure)

    @property
    def construct_type(self):
        """Return a description of the construct type.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `str`
                The construct type.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.construct_type
        'cell_measure'

        """
        return "cell_measure"

    def del_measure(self, default=ValueError()):
        """Remove the measure.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_measure`, `has_measure`, `set_measure`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the measure
                has not been set.

                {{default Exception}}

        :Returns:

                The removed measure.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_measure('area')
        >>> c.has_measure()
        True
        >>> c.get_measure()
        'area'
        >>> c.del_measure()
        'area'
        >>> c.has_measure()
        False
        >>> print(c.del_measure(None))
        None
        >>> print(c.get_measure(None))
        None

        """
        return self._del_component("measure", default=default)

    def has_measure(self):
        """Whether the measure has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_measure`, `get_measure`, `set_measure`

        :Returns:

             `bool`
                True if the measure has been set, otherwise False.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_measure('area')
        >>> c.has_measure()
        True
        >>> c.get_measure()
        'area'
        >>> c.del_measure()
        'area'
        >>> c.has_measure()
        False
        >>> print(c.del_measure(None))
        None
        >>> print(c.get_measure(None))
        None

        """
        return self._has_component("measure")

    def get_measure(self, default=ValueError()):
        """Return the measure.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_measure`, `has_measure`, `set_measure`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the measure
                has not been set.

                {{default Exception}}

        :Returns:

                The value of the measure.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_measure('area')
        >>> c.has_measure()
        True
        >>> c.get_measure()
        'area'
        >>> c.del_measure()
        'area'
        >>> c.has_measure()
        False
        >>> print(c.del_measure(None))
        None
        >>> print(c.get_measure(None))
        None

        """
        return self._get_component("measure", default=default)

    def set_measure(self, measure):
        """Set the measure.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_measure`, `get_measure`, `has_measure`

        :Parameters:

            measure: `str`
                The value for the measure.

        :Returns:

             `None`

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_measure('area')
        >>> c.has_measure()
        True
        >>> c.get_measure()
        'area'
        >>> c.del_measure()
        'area'
        >>> c.has_measure()
        False
        >>> print(c.del_measure(None))
        None
        >>> print(c.get_measure(None))
        None

        """
        return self._set_component("measure", measure, copy=False)
