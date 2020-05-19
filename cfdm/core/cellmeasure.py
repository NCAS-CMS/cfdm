from builtins import super

from . import abstract


class CellMeasure(abstract.PropertiesData):
    '''A cell measure construct of the CF data model.

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

    .. versionadded:: 1.7.0

    '''
    def __init__(self, measure=None, properties=None, data=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialisation**

    :Parameters:

        measure: `str`, optional
            Set the measure that indicates which metric given by the
            data array. Ignored if the *source* parameter is set.

            The measure may also be set after initialisation with the
            `set_measure` method.

            *Parameter example:*
              ``measure='area'``

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
              ``properties={'units': 'metres 2'}``

        data: `Data`, optional
            Set the data array. Ignored if the *source* parameter is
            set.

            The data array also may be set after initialisation with
            the `set_data` method.

        source: optional
            Initialise the *measure*, *properties* and *data*
            parameters (if present) from *source*, which will be a
            `CellMeasure` object, or a subclass of one of its parent
            classes.

            *Parameter example:*
              >>> d = CellMeasure(source=c)

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization By default parameters are deep copied.

        '''
        super().__init__(properties=properties, source=source,
                         data=data, copy=copy, _use_data=_use_data)

        if source is not None:
            try:
                measure = source.get_measure(None)
            except AttributeError:
                measure = None
        # --- End: if

        if measure is not None:
            self.set_measure(measure)

    @property
    def construct_type(self):
        '''Return a description of the construct type.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The construct type.

    **Examples:**

    >>> f.construct_type
    'cell_measure'

        '''
        return 'cell_measure'

    def del_measure(self, default=ValueError()):
        '''Remove the measure.

    .. versionadded:: 1.7.0

    .. seealso:: `get_measure`, `has_measure`, `set_measure`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the measure
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The removed measure.

    **Examples:**

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

        '''
        try:
            return self._del_component('measure')
        except ValueError:
            return self._default(default,
              "{!r} has no measure".format(self.__class__.__name__))

    def has_measure(self):
        '''Whether the measure has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_measure`, `get_measure`, `set_measure`

    :Returns:

         `bool`
            True if the measure has been set, otherwise False.

    **Examples:**

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
        '''
        return self._has_component('measure')

    def get_measure(self, default=ValueError()):
        '''Return the measure.

    .. versionadded:: 1.7.0

    .. seealso:: `del_measure`, `has_measure`, `set_measure`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the measure
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The value of the measure.

    **Examples:**

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

        '''
        try:
            return self._get_component('measure')
        except ValueError:
            return self._default(default,
              "{!r} has no measure".format(self.__class__.__name__))

    def set_measure(self, measure, copy=True):
        '''Set the measure.

    .. versionadded:: 1.7.0

    .. seealso:: `del_measure`, `get_measure`, `has_measure`

    :Parameters:

        measure: `str`
            The value for the measure.

        copy: `bool`, optional
            If True then set a deep copy of *measure*.

    :Returns:

         `None`

    **Examples:**

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
        '''
        return self._set_component('measure', measure, copy=copy)

# --- End: class
