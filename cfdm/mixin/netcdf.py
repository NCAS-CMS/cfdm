from builtins import object

from copy import deepcopy


class DeprecationError(Exception):
    pass


class NetCDF(object):
    '''Mixin class for storing simple netCDF elements.

    .. versionadded:: 1.7.0

    '''
    def _initialise_netcdf(self, source=None):
        '''Call this from inside the __init__ method of a class that inherits
    from this mixin class.

    :Parameters:

        source: optional
            Initialise the netCDF components from those of *source*.

    :Returns:

        `None`

    **Examples:**

    >>> f._initialise_netcdf(source)

        '''
        if source is None:
            netcdf = {}
        else:
            try:
                netcdf = source._get_component('netcdf', {})
            except AttributeError:
                netcdf = {}
            else:
                if netcdf:
                    netcdf = deepcopy(netcdf)
                else:
                    netcdf = {}
        # --- End: if

        self._set_component('netcdf', netcdf, copy=False)


# --- End: class


class NetCDFDimension(NetCDF):
    '''Mixin class for accessing the netCDF dimension name.

    .. versionadded:: 1.7.0

    '''
    def nc_del_dimension(self, default=ValueError()):
        '''Remove the netCDF dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_get_dimension`, `nc_has_dimension`,
                 `nc_set_dimension`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            dimension name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The removed netCDF dimension name.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_has_dimension()
    True
    >>> f.nc_get_dimension()
    'time'
    >>> f.nc_del_dimension()
    'time'
    >>> f.nc_has_dimension()
    False
    >>> print(f.nc_get_dimension(None))
    None
    >>> print(f.nc_del_dimension(None))
    None

        '''
        try:
            return self._get_component('netcdf').pop('dimension')
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF dimension name".format(
                    self.__class__.__name__))

    def nc_get_dimension(self, default=ValueError()):
        '''Return the netCDF dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_dimension`, `nc_has_dimension`,
                 `nc_set_dimension`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            dimension name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The netCDF dimension name.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_has_dimension()
    True
    >>> f.nc_get_dimension()
    'time'
    >>> f.nc_del_dimension()
    'time'
    >>> f.nc_has_dimension()
    False
    >>> print(f.nc_get_dimension(None))
    None
    >>> print(f.nc_del_dimension(None))
    None

        '''
        try:
            return self._get_component('netcdf')['dimension']
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF dimension name".format(
                    self.__class__.__name__))

    def nc_has_dimension(self):
        '''Whether the netCDF dimension name has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_dimension`, `nc_get_dimension`,
                 `nc_set_dimension`

    :Returns:

        `bool`
            `True` if the netCDF dimension name has been set,
            otherwise `False`.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_has_dimension()
    True
    >>> f.nc_get_dimension()
    'time'
    >>> f.nc_del_dimension()
    'time'
    >>> f.nc_has_dimension()
    False
    >>> print(f.nc_get_dimension(None))
    None
    >>> print(f.nc_del_dimension(None))
    None

        '''
        return 'dimension' in self._get_component('netcdf')

    def nc_set_dimension(self, value):
        '''Set the netCDF dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_dimension`, `nc_get_dimension`,
                 `nc_has_dimension`

    :Parameters:

        value: `str`
            The value for the netCDF dimension name.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_has_dimension()
    True
    >>> f.nc_get_dimension()
    'time'
    >>> f.nc_del_dimension()
    'time'
    >>> f.nc_has_dimension()
    False
    >>> print(f.nc_get_dimension(None))
    None
    >>> print(f.nc_del_dimension(None))
    None

        '''
        self._get_component('netcdf')['dimension'] = value


# --- End: class


class NetCDFVariable(NetCDF):
    '''Mixin class for accessing the netCDF variable name.

    .. versionadded:: 1.7.0

    '''
    def nc_del_variable(self, default=ValueError()):
        '''Remove the netCDF variable name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_get_variable`, `nc_has_variable`,
                 `nc_set_variable`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            variable name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The removed netCDF variable name.

    **Examples:**

    >>> f.nc_set_variable('tas')
    >>> f.nc_has_variable()
    True
    >>> f.nc_get_variable()
    'tas'
    >>> f.nc_del_variable()
    'tas'
    >>> f.nc_has_variable()
    False
    >>> print(f.nc_get_variable(None))
    None
    >>> print(f.nc_del_variable(None))
    None

        '''
        try:
            return self._get_component('netcdf').pop('variable')
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF variable name".format(
                    self.__class__.__name__))

    def nc_get_variable(self, default=ValueError()):
        '''Return the netCDF variable name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_variable`, `nc_has_variable`,
                 `nc_set_variable`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            variable name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The netCDF variable name. If unset then *default* is
            returned, if provided.

    **Examples:**

    >>> f.nc_set_variable('tas')
    >>> f.nc_has_variable()
    True
    >>> f.nc_get_variable()
    'tas'
    >>> f.nc_del_variable()
    'tas'
    >>> f.nc_has_variable()
    False
    >>> print(f.nc_get_variable(None))
    None
    >>> print(f.nc_del_variable(None))
    None

        '''
        try:
            return self._get_component('netcdf')['variable']
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF variable name".format(
                    self.__class__.__name__))

    def nc_has_variable(self):
        '''Whether the netCDF variable name has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_variable`, `nc_get_variable`,
                 `nc_set_variable`

    :Returns:

        `bool`
            `True` if the netCDF variable name has been set, otherwise
            `False`.

    **Examples:**

    >>> f.nc_set_variable('tas')
    >>> f.nc_has_variable()
    True
    >>> f.nc_get_variable()
    'tas'
    >>> f.nc_del_variable()
    'tas'
    >>> f.nc_has_variable()
    False
    >>> print(f.nc_get_variable(None))
    None
    >>> print(f.nc_del_variable(None))
    None

        '''
        return 'variable' in self._get_component('netcdf')

    def nc_set_variable(self, value):
        '''Set the netCDF variable name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_variable`, `nc_get_variable`,
                 `nc_has_variable`

    :Parameters:

        value: `str`
            The value for the netCDF variable name.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_set_variable('tas')
    >>> f.nc_has_variable()
    True
    >>> f.nc_get_variable()
    'tas'
    >>> f.nc_del_variable()
    'tas'
    >>> f.nc_has_variable()
    False
    >>> print(f.nc_get_variable(None))
    None
    >>> print(f.nc_del_variable(None))
    None

        '''
        self._get_component('netcdf')['variable'] = value


# --- End: class


class NetCDFSampleDimension(NetCDF):
    '''Mixin class for accessing the netCDF sample dimension name.

    .. versionadded:: 1.7.0

    '''
    def nc_del_sample_dimension(self, default=ValueError()):
        '''Remove the netCDF sample dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_get_sample_dimension`, `nc_has_sample_dimension`,
                 `nc_set_sample_dimension`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            sample dimension name has not been set. If set to an
            `Exception` instance then it will be raised instead.

    :Returns:

        `str`
            The removed netCDF sample dimension name.

    **Examples:**

    >>> f.nc_set_sample_dimension('time')
    >>> f.nc_has_sample_dimension()
    True
    >>> f.nc_get_sample_dimension()
    'time'
    >>> f.nc_del_sample_dimension()
    'time'
    >>> f.nc_has_sample_dimension()
    False
    >>> print(f.nc_get_sample_dimension(None))
    None
    >>> print(f.nc_del_sample_dimension(None))
    None

        '''
        try:
            return self._get_component('netcdf').pop('sample_dimension')
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF sample dimension name".format(
                    self.__class__.__name__))

    def nc_get_sample_dimension(self, default=ValueError()):
        '''Return the netCDF sample dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_sample_dimension`, `nc_has_sample_dimension`,
                 `nc_set_sample_dimension`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            sample dimension name has not been set. If set to an
            `Exception` instance then it will be raised instead.

    :Returns:

        `str`
            The netCDF sample dimension name.

    **Examples:**

    >>> f.nc_set_sample_dimension('time')
    >>> f.nc_has_sample_dimension()
    True
    >>> f.nc_get_sample_dimension()
    'time'
    >>> f.nc_del_sample_dimension()
    'time'
    >>> f.nc_has_sample_dimension()
    False
    >>> print(f.nc_get_sample_dimension(None))
    None
    >>> print(f.nc_del_sample_dimension(None))
    None

        '''
        try:
            return self._get_component('netcdf')['sample_dimension']
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF sample dimension name".format(
                    self.__class__.__name__))

    def nc_has_sample_dimension(self):
        '''Whether the netCDF sample dimension name has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_sample_dimension`, `nc_get_sample_dimension`,
                 `nc_set_sample_dimension`

    :Returns:

        `bool`
            `True` if the netCDF sample dimension name has been set,
            otherwise `False`.

    **Examples:**

    >>> f.nc_set_sample_dimension('time')
    >>> f.nc_has_sample_dimension()
    True
    >>> f.nc_get_sample_dimension()
    'time'
    >>> f.nc_del_sample_dimension()
    'time'
    >>> f.nc_has_sample_dimension()
    False
    >>> print(f.nc_get_sample_dimension(None))
    None
    >>> print(f.nc_del_sample_dimension(None))
    None

        '''
        return 'sample_dimension' in self._get_component('netcdf')

    def nc_set_sample_dimension(self, value):
        '''Set the netCDF sample dimension name.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_del_sample_dimension`, `nc_get_sample_dimension`,
                 `nc_has_sample_dimension`

    :Parameters:

        value: `str`
            The value for the netCDF sample dimension name.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_set_sample_dimension('time')
    >>> f.nc_has_sample_dimension()
    True
    >>> f.nc_get_sample_dimension()
    'time'
    >>> f.nc_del_sample_dimension()
    'time'
    >>> f.nc_has_sample_dimension()
    False
    >>> print(f.nc_get_sample_dimension(None))
    None
    >>> print(f.nc_del_sample_dimension(None))
    None

        '''
        self._get_component('netcdf')['sample_dimension'] = value


# --- End: class


class NetCDFGlobalAttributes(NetCDF):
    '''Mixin class for accessing netCDF global attributes.

    .. versionadded:: 1.7.0

    '''
    def nc_global_attributes(self, values=False):
        '''Return the selection of properties to be written as netCDF global
    attributes.

    When multiple field constructs are being written to the same file,
    it is only possible to create a netCDF global attribute from a
    property that has identical values for each field construct. If
    any field construct's property has a different value then the
    property will not be written as a netCDF global attribute, even if
    it has been selected as such, but will appear instead as
    attributes on the netCDF data variables corresponding to each
    field construct.

    The standard description-of-file-contents properties are always
    written as netCDF global attributes, if possible, so selecting
    them is optional.

    .. versionadded:: 1.7.0

    .. seealso:: `write`, `nc_clear_global_attributes`,
                 `nc_set_global_attribute`, `nc_set_global_attributes`

    :Parameters:

        values: `bool`, optional
            Return the value (rather than `None`) for any global
            attribute that has, by definition, the same value as a
            construct property.

            .. versionadded:: 1.8.2

    :Returns:

        `dict`
            The selection of properties requested for writting to
            netCDF global attributes.

    **Examples:**

    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None}
    >>> f.nc_set_global_attribute('foo')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None, 'foo': None}
    >>> f.nc_set_global_attribute('comment', 'global comment')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_global_attributes(values=True)
    {'Conventions': 'CF-1.8', 'comment': 'global_comment', 'foo': 'bar'}
    >>> f.nc_clear_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_global_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('global_attributes')

        if out is None:
            return {}

        out = out.copy()

        if values:
            # Replace a None value with the value from the variable
            # properties
            properties = self.properties()
            if properties:
                for prop, value in out.items():
                    if value is None and prop in properties:
                        out[prop] = properties[prop]
        # --- End: if

        return out

    def nc_clear_global_attributes(self):
        '''Remove the selection of properties to be written as netCDF global
    attributes.

    When multiple field constructs are being written to the same file,
    it is only possible to create a netCDF global attribute from a
    property that has identical values for each field construct. If
    any field construct's property has a different value then the
    property will not be written as a netCDF global attribute, even if
    it has been selected as such, but will appear instead as
    attributes on the netCDF data variables corresponding to each
    field construct.

    The standard description-of-file-contents properties are always
    written as netCDF global attributes, if possible, so selecting
    them is optional.

    .. versionadded:: 1.7.0

    .. seealso:: `write`, `nc_global_attributes`,
                 `nc_set_global_attribute`, `nc_set_global_attributes`

    :Returns:

        `dict`
            The removed selection of properties requested for writting
            to netCDF global attributes.

    **Examples:**

    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None}
    >>> f.nc_set_global_attribute('foo')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None, 'foo': None}
    >>> f.nc_set_global_attribute('comment', 'global comment')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_clear_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_global_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('global_attributes')

        if out is None:
            out = {}

        self._get_component('netcdf')['global_attributes'] = {}

        return out

    def nc_set_global_attribute(self, prop, value=None):
        '''Select a property to be written as a netCDF global attribute.

    When multiple field constructs are being written to the same file,
    it is only possible to create a netCDF global attribute from a
    property that has identical values for each field construct. If
    any field construct's property has a different value then the
    property will not be written as a netCDF global attribute, even if
    it has been selected as such, but will appear instead as
    attributes on the netCDF data variables corresponding to each
    field construct.

    The standard description-of-file-contents properties are always
    written as netCDF global attributes, if possible, so selecting
    them is optional.

    .. versionadded:: 1.7.0

    .. seealso:: `write`, `nc_global_attributes`,
                 `nc_clear_global_attributes`,
                 `nc_set_global_attributes`

    :Parameters:

        prop: `str`
            Select the property to be written (if possible) as a
            netCDF global attribute.

        value: optional
            The value of the netCDF global attribute, which will be
            created (if possible) in addition to the property as
            written to a netCDF data variable. If unset (or `None`)
            then this acts as an instruction to write the property (if
            possible) to a netCDF global attribute instead of to a
            netCDF data variable.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None}
    >>> f.nc_set_global_attribute('foo')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None, 'foo': None}
    >>> f.nc_set_global_attribute('comment', 'global comment')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_clear_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_global_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('global_attributes')

        if out is None:
            out = {}

        out[prop] = value

        self._get_component('netcdf')['global_attributes'] = out

    def nc_set_global_attributes(self, properties, copy=True):
        '''Set properties to be written as netCDF global attributes.

    When multiple field constructs are being written to the same file,
    it is only possible to create a netCDF global attribute from a
    property that has identical values for each field construct. If
    any field construct's property has a different value then the
    property will not be written as a netCDF global attribute, even if
    it has been selected as such, but will appear instead as
    attributes on the netCDF data variables corresponding to each
    field construct.

    The standard description-of-file-contents properties are always
    written as netCDF global attributes, if possible, so selecting
    them is optional.

    .. versionadded:: 1.7.10

    .. seealso:: `write`, `nc_clear_global_attributes`,
                 `nc_global_attributes`, `nc_set_global_attribute`

    :Parameters:

        properties: `dict`
            Set the properties be written as a netCDF global attribute
            from the dictionary supplied. The value of a netCDF global
            attribute, which will be created (if possible) in addition
            to the property as written to a netCDF data variable. If a
            value of `None` is used then this acts as an instruction
            to write the property (if possible) to a netCDF global
            attribute instead of to a netCDF data variable.

            *Parameter example:*
              ``properties={'Conventions': None, 'project': 'research'}``

        copy: `bool`, optional
            If False then any property values provided by the
            *properties* parameter are not copied before insertion. By
            default they are deep copied.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None}
    >>> f.nc_set_global_attributes({})
    >>> f.nc_set_global_attributes({'foo': None})
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': None, 'foo': None}
    >>> f.nc_set_global_attributes('comment', 'global comment')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': None}
    >>> f.nc_set_global_attributes('foo', 'bar')
    >>> f.nc_global_attributes()
    {'Conventions': None, 'comment': 'global_comment', 'foo': 'bar'}

        '''
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        out = self._get_component('netcdf').get('global_attributes')
        if out is None:
            out = {}

        out.update(properties)

        self._get_component('netcdf')['global_attributes'] = out


# --- End: class


class NetCDFUnlimitedDimensions(NetCDF):
    '''Mixin class for accessing netCDF unlimited dimensions.

    .. versionadded:: 1.7.0

    Deprecated at version 1.7.4

    '''
    def nc_unlimited_dimensions(self):
        '''Return the selection of domain axis constructs to be written as
    netCDF unlimited dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: 1.7.0

    Deprecated at version 1.7.4

    .. seealso:: `write`, `nc_clear_unlimited_dimensions`,
                 `nc_set_unlimited_dimensions`

    :Returns:

        `set`
            The selection of domain axis constructs to be written as
            netCDF unlimited dimensions.

    **Examples:**

    >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0'}
    >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_clear_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_unlimited_dimensions()
    set()

        '''
        raise DeprecationError(
            "Field.nc_unlimited_dimensions was deprecated at v1.7.4 "
            "and is no longer available. Use DomainAxis.nc_is_unlimited "
            "instead")

        out = self._get_component('netcdf').get('unlimited_dimensions')

        if out is None:
            return set()

        return set(out)

    def nc_set_unlimited_dimensions(self, axes):
        '''Select domain axis constructs to be written as netCDF unlimited
    dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: 1.7.0

    Deprecated at version 1.7.4

    .. seealso:: `write`, `nc_unlimited_dimensions`,
                 `nc_clear_unlimited_dimensions`

    :Parameters:

        axes: sequence of `str`, optional
            Select the domain axis constructs from the sequence
            provided. Domain axis constructs are identified by their
            construct identifiers.

            *Parameter example:*
              ``axes=['domainaxis0', 'domainaxis1']``

            *Parameter example:*
              ``axes=()``

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0'}
    >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_clear_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_unlimited_dimensions()
    set()

        '''
        raise DeprecationError(
            "Field.nc_set_unlimited_dimensions was deprecated at v1.7.4 "
            "and is no longer available. Use DomainAxis.nc_set_unlimited "
            "instead")

        out = self._get_component('netcdf').get('unlimited_dimensions')

        if out is None:
            out = set()
        else:
            out = set(out)

        out.update(axes)

        self._get_component('netcdf')['unlimited_dimensions'] = tuple(out)

    def nc_clear_unlimited_dimensions(self):
        '''Remove the selection of domain axis constructs to be written as
    netCDF unlimited dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: 1.7.0

    Deprecated at version 1.7.4

    .. seealso:: `write`, `nc_unlimited_dimensions`,
                 `nc_set_unlimited_dimensions`

    :Returns:

        `set`
            The selection of domain axis constructs that has been removed.

    **Examples:**

    >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0'}
    >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
    >>> f.nc_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_clear_unlimited_dimensions()
    {'domainaxis0', 'domainaxis1'}
    >>> f.nc_unlimited_dimensions()
    set()

        '''
        raise DeprecationError(
            "Field.nc_clear_unlimited_dimensions was deprecated at v1.7.4 "
            "and is no longer available. Use DomainAxis.nc_set_unlimited "
            "instead")

        out = self._get_component('netcdf').get('unlimited_dimensions')

        if out is None:
            out = set()
        else:
            out = set(out)

        self._get_component('netcdf')['unlimited_dimensions'] = ()

        return out


# --- End: class


class NetCDFExternal(NetCDF):
    '''Mixin class for accessing the netCDF external variable status.

    .. versionadded:: 1.7.0

    '''
    def nc_get_external(self):
        '''Whether the construct corresponds to an external netCDF variable.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_set_external`

    :Returns:

        `bool`
            The external status.

    **Examples:**

    >>> c.nc_get_external()
    False
    >>> c.nc_set_external(True)
    >>> c.nc_get_external()
    True

        '''
        return self._get_component('netcdf').get('external', False)

    def nc_set_external(self, external):
        '''Set external status of a netCDF variable.

    .. versionadded:: 1.7.0

    .. seealso:: `nc_get_external`

    :Parameters:

        external: `bool`, optional
            Set the external status.

            *Parameter example:*
              ``external=True``

    :Returns:

        `None`

    **Examples:**

    >>> c.nc_get_external()
    False
    >>> c.nc_set_external(True)
    >>> c.nc_get_external()
    True

        '''
        self._get_component('netcdf')['external'] = bool(external)


# --- End: class

class NetCDFGeometry(NetCDF):
    '''Mixin class for accessing the netCDF geometry container variable
    name.

    .. versionadded:: 1.8.0

    '''
    def nc_del_geometry_variable(self, default=ValueError()):
        '''Remove the netCDF geometry container variable name.

    .. versionadded:: 1.8.0

    .. seealso:: `nc_get_geometry_variable`,
                 `nc_has_geometry_variable`,
                 `nc_set_geometry_variable`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            dimension name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The removed netCDF geometry container variable name.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry')
    >>> f.nc_has_geometry_variable()
    True
    >>> f.nc_get_geometry_variable()
    'geometry'
    >>> f.nc_del_geometry_variable()
    'geometry'
    >>> f.nc_has_geometry_variable()
    False
    >>> print(f.nc_get_geometry_variable(None))
    None
    >>> print(f.nc_del_geometry_variable(None))
    None

        '''
        try:
            return self._get_component('netcdf').pop('geometry_variable')
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF geometry variable name".format(
                    self.__class__.__name__))

    def nc_get_geometry_variable(self, default=ValueError()):
        '''Return the netCDF geometry container variable name.

    .. versionadded:: 1.8.0

    .. seealso:: `nc_del_geometry_variable`,
                 `nc_has_geometry_variable`,
                 `nc_set_geometry_variable`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the netCDF
            dimension name has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The netCDF geometry container variable name.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry')
    >>> f.nc_has_geometry_variable()
    True
    >>> f.nc_get_geometry_variable()
    'geometry'
    >>> f.nc_del_geometry_variable()
    'geometry'
    >>> f.nc_has_geometry_variable()
    False
    >>> print(f.nc_get_geometry_variable(None))
    None
    >>> print(f.nc_del_geometry_variable(None))
    None

        '''
        try:
            return self._get_component('netcdf')['geometry_variable']
        except KeyError:
            return self._default(
                default,
                "{!r} has no netCDF geometry variable name".format(
                    self.__class__.__name__))

    def nc_has_geometry_variable(self):
        '''Whether the netCDF geometry container variable name has been set.

    .. versionadded:: 1.8.0

    .. seealso:: `nc_del_geometry_variable`,
                 `nc_get_geometry_variable`,
                 `nc_set_geometry_variable`

    :Returns:
        `bool`
            `True` if the netCDF geometry container variable name has
            been set, otherwise `False`.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry')
    >>> f.nc_has_geometry_variable()
    True
    >>> f.nc_get_geometry_variable()
    'geometry'
    >>> f.nc_del_geometry_variable()
    'geometry'
    >>> f.nc_has_geometry_variable()
    False
    >>> print(f.nc_get_geometry_variable(None))
    None
    >>> print(f.nc_del_geometry_variable(None))
    None

        '''
        return 'geometry_variable' in self._get_component('netcdf')

    def nc_set_geometry_variable(self, value):
        '''Set the netCDF geometry container variable name.

    .. versionadded:: 1.8.0

    .. seealso:: `nc_del_geometry_variable`,
                 `nc_get_geometry_variable`,
                 `nc_has_geometry_variable`

    :Parameters:

        value: `str`
            The value for the netCDF geometry container variable name.

    :Returns:
        `None`

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry')
    >>> f.nc_has_geometry_variable()
    True
    >>> f.nc_get_geometry_variable()
    'geometry'
    >>> f.nc_del_geometry_variable()
    'geometry'
    >>> f.nc_has_geometry_variable()
    False
    >>> print(f.nc_get_geometry_variable(None))
    None
    >>> print(f.nc_del_geometry_variable(None))
    None

        '''
        self._get_component('netcdf')['geometry_variable'] = value

# --- End: class


class NetCDFHDF5(NetCDF):
    '''Mixin class for TODO

    .. versionadded:: 1.7.2

    '''
    def nc_hdf5_chunksizes(self):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: 1.7.2

    .. seealso:: `nc_clear_hdf5_chunksizes`, `nc_set_hdf5_chunksizes`

    :Returns:

        `tuple`
            TODO The chunk sizes prior to the new setting, or the current
            current sizes if no new values are specified.

    **Examples:**

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        return self._get_component('netcdf').get('hdf5_chunksizes', ())

    def nc_clear_hdf5_chunksizes(self):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: 1.7.2

    .. seealso:: `nc_hdf5_chunksizes`, `nc_set_hdf5_chunksizes`

    :Returns:

        `tuple`
            TODO

    **Examples:**

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        return self._get_component('netcdf').pop('hdf5_chunksizes', ())

    def nc_set_hdf5_chunksizes(self, chunksizes):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: 1.7.2

    .. seealso:: `nc_hdf5_chunksizes`, `nc_clear_hdf5_chunksizes`

    :Parameters:

        chunksizes: sequence of `int`
            The chunksizes for each dimension. Can be integers from 0
            to the dimension size.

    :Returns:

        `None`

    **Examples:**

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        try:
            shape = self.shape
        except AttributeError:
            pass
        else:
            if len(chunksizes) != len(shape):
                raise ValueError(
                    "chunksizes must be a sequence with the same length "
                    "as dimensions")

            for i, j in zip(chunksizes, shape):
                if i < 0:
                    raise ValueError("chunksize cannot be negative")
                if i > j:
                    raise ValueError("chunksize cannot exceed dimension size")
        # --- End: try

        self._get_component('netcdf')['hdf5_chunksizes'] = tuple(chunksizes)


# --- End: class

class NetCDFHDF5_exp(NetCDF):
    '''Mixin class for TODO

    .. versionadded:: 1.7.2

    '''
    def nc_del_hdf5_chunksize(self, default=ValueError()):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape, and chunksizes are ignored for
              netCDF3 files that do not use HDF5.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_get_hdf5_chunksize`, `nc_has_hdf5_chunksize`,
                 `nc_set_hdf5_chunksize`

    :Returns:

            TODO

    **Examples:**

    TODO

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        return 'hdf5_chunksize' in self._get_component('netcdf')

    def nc_get_hdf5_chunksize(self, default=ValueError()):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape, and chunksizes are ignored for
              netCDF3 files that do not use HDF5.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_del_hdf5_chunksize`, `nc_has_hdf5_chunksize`,
                 `nc_set_hdf5_chunksize`

    :Returns:

            TODO The chunk sizes prior to the new setting, or the current
            current sizes if no new values are specified.

    **Examples:**

    TODO

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        try:
            return self._get_component('netcdf')['hdf5_chunksize']
        except KeyError:
            return self._default(
                default,
                "{!r} has no HDF5 chunksize".format(
                    self.__class__.__name__))

    def nc_has_hdf5_chunksize(self):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape, and chunksizes are ignored for
              netCDF3 files that do not use HDF5.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_del_hdf5_chunksize`, `nc_get_hdf5_chunksize`,
                 `nc_set_hdf5_chunksize`

    :Returns:

        `bool`
            TODO The chunk sizes prior to the new setting, or the current
            current sizes if no new values are specified.

    **Examples:**

    TODO

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        return 'hdf5_chunksize' in self._get_component('netcdf')

    def nc_set_hdf5_chunksize(self, value):
        '''TODO

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape, and chunksizes are ignored for
              netCDF3 files that do not use HDF5.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_del_hdf5_chunksize`, `nc_get_hdf5_chunksize`,
                 `nc_has_hdf5_chunksize`

    :Parameters:

        value: `int`
            TODO

    :Returns:

        `None`

    **Examples:**

    TODO

    >>> d.shape
    (1, 96, 73)
    >>> d.nc_set_hdf5_chunksizes([1, 48, 73])
    >>> d.nc_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_clear_hdf5_chunksizes()
    (1, 48, 73)
    >>> d.nc_hdf5_chunksizes()
    ()

        '''
        self._get_component('netcdf')['hdf5_chunksize'] = int(value)


# --- End: class

class NetCDFUnlimitedDimension(NetCDF):
    '''Mixin class for accessing a netCDF unlimited dimension.

    .. versionadded:: 1.7.4

    '''
    def nc_is_unlimited(self):
        '''Inspect the unlimited status of the a netCDF dimension.

    By default output netCDF dimensions are not unlimited. The status
    is used by the `write` function.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_set_unlimited`

    :Returns:

        `bool`
            The existing unlimited status. True and False signify
            "unlimited" and "not unlimited" repectively.

    **Examples:**

    >>> da = f.domain_axis('domainaxis1')
    >>> da.nc_is_unlimited()
    False
    >>> da.nc_set_unlimited(True)
    >>> da.nc_is_unlimited()
    True
    >>> da.nc_set_unlimited(False)
    False
    >>> da.nc_is_unlimited()
    True

        '''
        return self._get_component('netcdf').get('unlimited', False)

    def nc_set_unlimited(self, value):
        '''Set the unlimited status of the a netCDF dimension.

    By default output netCDF dimensions are not unlimited. The status
    is used by the `write` function.

    .. versionadded:: 1.7.4

    .. seealso:: `nc_is_unlimited`

    :Parameters:

        value: `bool`
            The new unlimited status. True and False signify
            "unlimited" and "not unlimited" repectively.

    :Returns:

        `None`

    **Examples:**

    >>> da = f.domain_axis('domainaxis1')
    >>> da.nc_is_unlimited()
    False
    >>> da.nc_set_unlimited(True)
    >>> da.nc_is_unlimited()
    True
    >>> da.nc_set_unlimited(False)
    False
    >>> da.nc_is_unlimited()
    True

        '''
        self._get_component('netcdf')['unlimited'] = bool(value)

# --- End: class
