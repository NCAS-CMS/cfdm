from builtins import super

from copy import deepcopy

from . import mixin
from . import core


class Bounds(mixin.NetCDFVariable,
             mixin.NetCDFDimension,
             mixin.PropertiesData,
             core.Bounds):
    '''A cell bounds component of a coordinate or domain ancillary
    construct of the CF data model.

    An array of cell bounds spans the same domain axes as its
    coordinate array, with the addition of an extra dimension whose
    size is that of the number of vertices of each cell. This extra
    dimension does not correspond to a domain axis construct since it
    does not relate to an independent axis of the domain. Note that,
    for climatological time axes, the bounds are interpreted in a
    special way indicated by the cell method constructs.

    In the CF data model, a bounds component does not have its own
    properties because they can not logically be different to those of
    the coordinate construct itself. However, it is sometimes desired
    to store attributes on a CF-netCDF bounds variable, so it is also
    allowed to provide properties to a bounds component.

    **NetCDF interface**

    The netCDF variable name of the bounds may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The name of the trailing netCDF dimension spanned by bounds (which
    does not correspond to a domain axis construct) may be accessed
    with the `nc_set_dimension`, `nc_get_dimension`,
    `nc_del_dimension` and `nc_has_dimension` methods.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, source=None,
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
                 ``properties={'standard_name': 'grid_latitude'}``

        data: `Data`, optional
            Set the data. Ignored if the *source* parameter is set.

            The data also may be set after initialisation with the
            `set_data` method.

        source: optional
            Initialize the properties and data from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)

        if source is not None:
            try:
                inherited_properties = source.inherited_properties()
            except AttributeError:
                inherited_properties = {}
        else:
            inherited_properties = {}

        self._set_component('inherited_properties', inherited_properties)

        self._initialise_netcdf(source)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def dump(self, display=True, _key=None, _title=None,
             _create_title=True, _prefix='', _level=0,
             _omit_properties=None, _axes=None, _axis_names=None):
        '''A full description of the bounds component.

    Returns a description of all properties and provides selected
    values of all data arrays.

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
        if _create_title and _title is None:
            _title = 'Bounds: ' + self.identity(default='')

        return super().dump(display=display, _key=_key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title, _axes=_axes,
                            _axis_names=_axis_names)

    def get_data(self, default=ValueError(), _units=True,
                 _fill_value=True):
        '''Return the data.

    Note that the data are returned in a `Data` object. Use the
    `array` attribute of the `Data` instance to return the data as an
    independent `numpy` array.

    .. versionadded:: 1.7.0

    .. seealso:: `data`, `del_data`, `has_data`, `set_data`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

            The data.

    **Examples:**

    >>> d = cfdm.Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> f.get_data()
    <Data(10): [0, ..., 9]>
    >>> f.del_data()
    <Data(10): [0, ..., 9]>
    >>> f.has_data()
    False
    >>> print(f.get_data(None))
    None
    >>> print(f.del_data(None))
    None

        '''
        data = super().get_data(default=None, _units=_units,
                                _fill_value=_fill_value)

        if data is None:
            return super().get_data(default=default)

        if _units:
            if not data.has_units():
                units = self.inherited_properties().get('units')
                if units is not None:
                    data.set_units(units)
            # --- End: if

            if not data.has_calendar():
                calendar = self.inherited_properties().get('calendar')
                if calendar is not None:
                    data.set_calendar(calendar)
        # --- End: if

        if _fill_value:
            if not data.has_fill_value():
                _ = self.inherited_properties().get('fill_value')  # TODO
                if _ is not None:
                    data.set_fill_value(_)
        # --- End: if

        return data

    def inherited_properties(self):
        '''Return the properties inherited from a coordinate construct.

    .. versionadded:: 1.7.0

    .. seealso:: `properties`

    :Returns:

        `dict`
            The inherited properties.

    **Examples:**

    >>> b.properties()
    {}
    >>> b.inherited_properties()
    {'standard_name': 'longitude',
     'units': 'degrees_east'}

        '''
        return deepcopy(self._get_component('inherited_properties', {}))

    def identity(self, default=''):
        '''Return the canonical identity.

    By default the identity is the first found of the following:

    1. The ``standard_name`` property.
    2. The ``cf_role`` property, preceeded by ``'cf_role='``.
    3. The ``long_name`` property, preceeded by ``'long_name='``.
    4. The netCDF variable name, preceeded by ``'ncvar%'``.
    5. The value of the *default* parameter.

    Properties include any inherited properties.

    .. versionadded:: 1.7.0

    .. seealso:: `identities`

    :Parameters:

        default: optional
            If no identity can be found then return the value of the
            default parameter.

    :Returns:

            The identity.

    **Examples:**

    >>> b.inherited_properties()
    {'foo': 'bar',
     'long_name': 'Longitude'}
    >>> b.properties()
    {'long_name': 'A different long name'}
    >>> b.identity()
    'long_name=A different long name'
    >>> b.del_property('long_name')
    'A different long name'
    >>> b.identity()
    'long_name=Longitude'

        '''
        inherited_properties = self.inherited_properties()
        if inherited_properties:
            bounds = self.copy()
            properties = bounds.properties()
            bounds.set_properties(inherited_properties)
            bounds.set_properties(properties)
            self = bounds

        return super().identity(default=default)

# --- End: class
