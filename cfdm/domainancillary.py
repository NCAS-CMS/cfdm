from builtins import super

from . import mixin
from . import core


class DomainAncillary(mixin.NetCDFVariable,
                      mixin.PropertiesDataBounds,
                      core.DomainAncillary):
    '''A domain ancillary construct of the CF data model.

    A domain ancillary construct provides information which is needed
    for computing the location of cells in an alternative coordinate
    system. It is referenced by a term of a coordinate conversion
    formula of a coordinate reference construct. It contains a data
    array which depends on zero or more of the domain axes.

    It also contains an optional array of cell bounds, stored in a
    `Bounds` object, recording the extents of each cell (only
    applicable if the array contains coordinate data), and properties
    to describe the data.

    An array of cell bounds spans the same domain axes as the data
    array, with the addition of an extra dimension whose size is that
    of the number of vertices of each cell.

    **NetCDF interface**

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
           Set descriptive properties. The dictionary keys are
           property names, with corresponding values. Ignored if the
           *source* parameter is set.

           Properties may also be set after initialisation with the
           `set_properties` and `set_property` methods.

           *Parameter example:*
              ``properties={'standard_name': 'altitude'}``

        data: `Data`, optional
            Set the data array. Ignored if the *source* parameter is
            set.

            The data array may also be set after initialisation with
            the `set_data` method.

        bounds: `Bounds`, optional
            Set the bounds array. Ignored if the *source* parameter is
            set.

            The bounds array may also be set after initialisation with
            the `set_bounds` method.

        source: optional
            Initialize the properties, data and bounds from those of
            *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, data=data,
                         bounds=bounds, geometry=geometry,
                         interior_ring=interior_ring, source=source,
                         copy=copy, _use_data=_use_data)

        self._initialise_netcdf(source)


    def dump(self, display=True, _omit_properties=None, _key=None,
             _level=0, _title=None, _axes=None, _axis_names=None):
        '''A full description of the domain ancillary construct.

    Returns a description of all properties, including those of
    components, and provides selected values of all data arrays.

    .. versionadded:: 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        `None` or `str`
            The description. If *display* is True then the description
            is printed and `None` is returned. Otherwise the
            description is returned as a string.

        '''
        if _title is None:
            ncvar = self.nc_get_variable(None)
            if ncvar is not None:
                ncvar = ' (ncvar%{0})'.format(ncvar)
            else:
                ncvar = ''

            if _key is None:
                default = ''
            else:
                default = _key

            _title = 'Domain Ancillary: ' + self.identity(default=default) + ncvar


        return super().dump(display=display,
                            _omit_properties=_omit_properties,
                            _key=_key, _level=_level, _title=_title,
                            _axes=_axes, _axis_names=_axis_names)


    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=True,
               ignore_type=False):
        '''Whether two domain ancillary constructs are the same.

    Equality is strict by default. This means that:

    * the same descriptive properties must be present, with the same
      values and data types, and vector-valued properties must also
      have same the size and be element-wise equal (see the
      *ignore_properties* and *ignore_data_type* parameters), and

    ..

    * if there are data arrays then they must have same shape and data
      type, the same missing data mask, and be element-wise equal (see
      the *ignore_data_type* parameter).

    ..

    * if there are bounds then their descriptive properties (if any)
      must be the same and their data arrays must have same shape and
      data type, the same missing data mask, and be element-wise equal
      (see the *ignore_properties* and *ignore_data_type* parameters).

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. See the *atol* and
    *rtol* parameters.

    Any compression is ignored by default, with only the arrays in
    their uncompressed forms being compared. See the
    *ignore_compression* parameter.

    Any type of object may be tested but, in general, equality is only
    possible with another domain ancillary construct, or a subclass of
    one. See the *ignore_type* parameter.

    NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked.

    .. versionadded:: 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `cfdm.ATOL`
            function.

        rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `cfdm.RTOL`
            function.

        ignore_fill_value: `bool`, optional
            If True then the ``_FillValue`` and ``missing_value``
            properties are omitted from the comparison.

        verbose: `int` or `None`, optional
            If an integer from ``0`` to ``3``, corresponding to increasing
            verbosity (else ``-1`` as a special case of maximal and extreme
            verbosity), set for the duration of the method call (only) as
            the minimum severity level cut-off of displayed log messages,
            regardless of the global configured `cfdm.LOG_LEVEL`.

            Else, if `None` (the default value), log messages will be
            filtered out, or otherwise, according to the value of the
            `cfdm.LOG_LEVEL` setting.

            Overall, the higher a non-negative integer that is set (up to
            a maximum of ``3``) the more description that is printed to
            convey information about differences that lead to inequality.

        ignore_properties: sequence of `str`, optional
            The names of properties to omit from the comparison.

        ignore_data_type: `bool`, optional
            If True then ignore the data types in all numerical
            comparisons. By default different numerical data types
            imply inequality, regardless of whether the elements are
            within the tolerance for equality.

        ignore_compression: `bool`, optional
            If False then the compression type and, if applicable, the
            underlying compressed arrays must be the same, as well as
            the arrays in their uncompressed forms. By default only
            the arrays in their uncompressed forms are compared.

        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another domain ancillary construct,
            or a subclass of one. If *ignore_type* is True then
            ``DomainAncillary(source=other)`` is tested, rather than
            the ``other`` defined by the *other* parameter.

    :Returns:

        `bool`
            Whether the two domain ancillary constructs are equal.

    **Examples:**

    >>> f.equals(f)
    True
    >>> f.equals(f.copy())
    True
    >>> f.equals('not a domain ancillary')
    False

    >>> g = f.copy()
    >>> g.set_property('foo', 'bar')
    >>> f.equals(g)
    False
    >>> f.equals(g, verbose=3)
    DomainAncillary: Non-common property name: foo
    DomainAncillary: Different properties
    False

        '''
        return super().equals(other, rtol=rtol, atol=atol,
                              verbose=verbose,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              ignore_properties=ignore_properties,
                              ignore_compression=ignore_compression,
                              ignore_type=ignore_type)

# --- End: class
