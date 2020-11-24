from copy import deepcopy


class DeprecationError(Exception):
    pass


class NetCDF:
    '''Mixin class for storing simple netCDF elements.

    .. versionadded:: (cfdm) 1.7.0

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


class _NetCDFGroupsMixin():
    '''Mixin class for accessing netCDF(4) hierarchical groups.

    .. versionadded:: (cfdm) 1.8.6
    '''
    def _nc_groups(self, nc_get):
        '''Return the netCDF group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `_nc_clear_groups`, `_nc_set_groups`

    :Parameters:

        nc_get: function
            The method which gets the netCDF name.

    :Returns:

        `tuple` of `str`
            The group structure.

    **Examples:**

    See the examples in classes which inherit this method.

        '''
        name = nc_get(default='')
        return tuple(name.split('/')[1:-1])

    def _nc_set_groups(self, groups, nc_get, nc_set, nc_groups):
        '''Set the netCDF group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `_nc_clear_groups`, `_nc_groups`

    :Parameters:

        groups: sequence of `str`
            The new group structure.

        nc_get: function
            The method which gets the netCDF name.

        nc_set: function
            The method which sets the netCDF name.

        nc_groups: function
            The method which returns existing group structure.

    :Returns:

        `tuple` of `str`
            The group structure prior to being reset.

    **Examples:**

    See the examples in classes which inherit this method.

        '''
        old = nc_groups()

        name = nc_get(default='')
        name = name.split('/')[-1]
        if not name:
            raise ValueError(
                "Can't set groups when there is no netCDF name")

        if groups:
            for group in groups:
                if '/' in group:
                    raise ValueError(
                        "Can't have '/' character in group name: "
                        "{!r}".format(group))
            # --- End: for

            name = '/'.join(('',) + tuple(groups) + (name,))

        if name:
            nc_set(name)

        return old

    def _nc_clear_groups(self, nc_get, nc_set, nc_groups):
        '''Remove the netCDF group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `_nc_groups`, `_nc_set_groups`

    :Parameters:

        nc_get: function
            The method which gets the netCDF name.

        nc_set: function
            The method which sets the netCDF name.

        nc_groups: function
            The method which returns existing group structure.

    :Returns:

        `tuple` of `str`
            The removed group structure.

    **Examples:**

    See the examples in classes which inherit this method.

        '''
        old = nc_groups()

        name = nc_get(default='')
        name = name.split('/')[-1]
        if name:
            nc_set(name)

        return old


class NetCDFDimension(NetCDF,
                      _NetCDFGroupsMixin):
    '''Mixin class for accessing the netCDF dimension name.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def nc_del_dimension(self, default=ValueError()):
        '''Remove the netCDF dimension name.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    If there are any ``/`` (slash) characters in the netCDF name then
    these act as delimiters for a group hierarchy. By default, or if
    the name starts with a ``/`` character and contains no others, the
    name is assumed to be in the root group.

    .. versionadded:: (cfdm) 1.7.0

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
        if not value or value == '/':
            raise ValueError(
                "Invalid netCDF dimension name: {!r}".format(value))

        if '/' in value:
            if not value.startswith('/'):
                raise ValueError(
                    "A netCDF dimension name with a group structure "
                    "must start with a '/'. Got {!r}".format(value)
                )

            if value.count('/') == 1:
                value = value[1:]
            elif value.endswith('/'):
                raise ValueError(
                    "A netCDF dimension name with a group structure "
                    "can't end with a '/'. Got {!r}".format(value)
                )
        # --- End: if

        self._get_component('netcdf')['dimension'] = value

    def nc_dimension_groups(self):
        '''Return the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_dimension_groups`,
                 `nc_set_dimension_groups`

    :Returns:

        `tuple` of `str`
            The group structure.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_dimension_groups()
    ()
    >>> f.nc_set_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    '/forecast/model/time'
    >>> f.nc_clear_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    'time'

    >>> f.nc_set_dimension('/forecast/model/time')
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_dimension('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_dimension_groups()
    ()

        '''
        return self._nc_groups(nc_get=self.nc_get_dimension)

    def nc_set_dimension_groups(self, groups):
        '''Set the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for setting the group structure is to set
    the netCDF dimension name, with `nc_set_dimension`, with the group
    structure delimited by ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_dimension_groups`, `nc_dimension_groups`

    :Parameters:

        groups: sequence of `str`
            The new group structure.

    :Returns:

        `tuple` of `str`
            The group structure prior to being reset.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_dimension_groups()
    ()
    >>> f.nc_set_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    '/forecast/model/time'
    >>> f.nc_clear_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    'time'

    >>> f.nc_set_dimension('/forecast/model/time')
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_dimension('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_dimension_groups()
    ()

        '''
        return self._nc_set_groups(groups,
                                   nc_get=self.nc_get_dimension,
                                   nc_set=self.nc_set_dimension,
                                   nc_groups=self.nc_dimension_groups)

    def nc_clear_dimension_groups(self):
        '''Remove the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for removing the group structure is to
    set the netCDF dimension name, with `nc_set_dimension`, with no
    ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_dimension_groups`, `nc_set_dimension_groups`

    :Returns:

        `tuple` of `str`
            The removed group structure.

    **Examples:**

    >>> f.nc_set_dimension('time')
    >>> f.nc_dimension_groups()
    ()
    >>> f.nc_set_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    '/forecast/model/time'
    >>> f.nc_clear_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_dimension()
    'time'

    >>> f.nc_set_dimension('/forecast/model/time')
    >>> f.nc_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_dimension('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_dimension_groups()
    ()

        '''
        return self._nc_clear_groups(
            nc_get=self.nc_get_dimension,
            nc_set=self.nc_set_dimension,
            nc_groups=self.nc_dimension_groups)

# --- End: class


class NetCDFVariable(NetCDF,
                     _NetCDFGroupsMixin):
    '''Mixin class for accessing the netCDF variable name.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def nc_del_variable(self, default=ValueError()):
        '''Remove the netCDF variable name.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    If there are any ``/`` (slash) characters in the netCDF name then
    these act as delimiters for a group hierarchy. By default, or if
    the name starts with a ``/`` character and contains no others, the
    name is assumed to be in the root group.

    .. versionadded:: (cfdm) 1.7.0

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
        if not value or value == '/':
            raise ValueError(
                "Invalid netCDF variable name: {!r}".format(value))

        if '/' in value:
            if not value.startswith('/'):
                raise ValueError(
                    "A netCDF variable name with a group structure "
                    "must start with a '/'. Got {!r}".format(value)
                )

            if value.count('/') == 1:
                value = value[1:]
            elif value.endswith('/'):
                raise ValueError(
                    "A netCDF variable name with a group structure "
                    "can't end with a '/'. Got {!r}".format(value)
                )
        # --- End: if

        self._get_component('netcdf')['variable'] = value

    def nc_variable_groups(self):
        '''Return the netCDF variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_variable_groups`,
                 `nc_set_variable_groups`

    :Returns:

        `tuple` of `str`
            The group structure.

    **Examples:**

    >>> f.nc_set_variable('time')
    >>> f.nc_variable_groups()
    ()
    >>> f.nc_set_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    '/forecast/model/time'
    >>> f.nc_clear_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    'time'

    >>> f.nc_set_variable('/forecast/model/time')
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_del_variable('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_variable_groups()
    ()

        '''
        return self._nc_groups(nc_get=self.nc_get_variable)

    def nc_set_variable_groups(self, groups):
        '''Set the netCDF variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for setting the group structure is to set
    the netCDF variable name, with `nc_set_variable`, with the group
    structure delimited by ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_variable_groups`, `nc_variable_groups`

    :Parameters:

        groups: sequence of `str`
            The new group structure.

    :Returns:

        `tuple` of `str`
            The group structure prior to being reset.

    **Examples:**

    >>> f.nc_set_variable('time')
    >>> f.nc_variable_groups()
    ()
    >>> f.nc_set_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    '/forecast/model/time'
    >>> f.nc_clear_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    'time'

    >>> f.nc_set_variable('/forecast/model/time')
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_del_variable('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_variable_groups()
    ()

        '''
        return self._nc_set_groups(groups,
                                   nc_get=self.nc_get_variable,
                                   nc_set=self.nc_set_variable,
                                   nc_groups=self.nc_variable_groups)

    def nc_clear_variable_groups(self):
        '''Remove the netCDF variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for removing the group structure is to
    set the netCDF variable name, with `nc_set_variable`, with no
    ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_variable_groups`, `nc_set_variable_groups`

    :Returns:

        `tuple` of `str`
            The removed group structure.

    **Examples:**

    >>> f.nc_set_variable('time')
    >>> f.nc_variable_groups()
    ()
    >>> f.nc_set_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    '/forecast/model/time'
    >>> f.nc_clear_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_variable()
    'time'

    >>> f.nc_set_variable('/forecast/model/time')
    >>> f.nc_variable_groups()
    ('forecast', 'model')
    >>> f.nc_del_variable('/forecast/model/time')
    '/forecast/model/time'
    >>> f.nc_variable_groups()
    ()

        '''
        return self._nc_clear_groups(
            nc_get=self.nc_get_variable,
            nc_set=self.nc_set_variable,
            nc_groups=self.nc_variable_groups)

# --- End: class


class NetCDFSampleDimension(NetCDF,
                            _NetCDFGroupsMixin):
    '''Mixin class for accessing the netCDF sample dimension name.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def nc_del_sample_dimension(self, default=ValueError()):
        '''Remove the netCDF sample dimension name.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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

    If there are any ``/`` (slash) characters in the netCDF name then
    these act as delimiters for a group hierarchy. By default, or if
    the name starts with a ``/`` character and contains no others, the
    name is assumed to be in the root group.

    .. versionadded:: (cfdm) 1.7.0

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
        if not value or value == '/':
            raise ValueError(
                "Invalid netCDF sample dimension name: {!r}".format(value))

        if '/' in value:
            if not value.startswith('/'):
                raise ValueError(
                    "A netCDF sample dimension name with a group structure "
                    "must start with a '/'. Got {!r}".format(value)
                )

            if value.count('/') == 1:
                value = value[1:]
            elif value.endswith('/'):
                raise ValueError(
                    "A netCDF sample dimension name with a group structure "
                    "can't end with a '/'. Got {!r}".format(value)
                )
        # --- End: if

        self._get_component('netcdf')['sample_dimension'] = value

    def nc_sample_dimension_groups(self):
        '''Return the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_sample_dimension_groups`,
                 `nc_set_sample_dimension_groups`

    :Returns:

        `tuple` of `str`
            The group structure.

    **Examples:**

    >>> f.nc_set_sample_dimension('element')
    >>> f.nc_sample_dimension_groups()
    ()
    >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    '/forecast/model/element'
    >>> f.nc_clear_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    'element'

    >>> f.nc_set_sample_dimension('/forecast/model/element')
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_sample_dimension('/forecast/model/element')
    '/forecast/model/element'
    >>> f.nc_sample_dimension_groups()
    ()

        '''
        return self._nc_groups(nc_get=self.nc_get_sample_dimension)

    def nc_set_sample_dimension_groups(self, groups):
        '''Set the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for setting the group structure is to set
    the netCDF dimension name, with `nc_set_sample_dimension`, with
    the group structure delimited by ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_sample_dimension_groups`,
                 `nc_sample_dimension_groups`

    :Parameters:

        groups: sequence of `str`
            The new group structure.

    :Returns:

        `tuple` of `str`
            The group structure prior to being reset.

    **Examples:**

    >>> f.nc_set_sample_dimension('element')
    >>> f.nc_sample_dimension_groups()
    ()
    >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    '/forecast/model/element'
    >>> f.nc_clear_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    'element'

    >>> f.nc_set_sample_dimension('/forecast/model/element')
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_sample_dimension('/forecast/model/element')
    '/forecast/model/element'
    >>> f.nc_sample_dimension_groups()
    ()

        '''
        return self._nc_set_groups(groups,
                                   nc_get=self.nc_get_sample_dimension,
                                   nc_set=self.nc_set_sample_dimension,
                                   nc_groups=self.nc_sample_dimension_groups)

    def nc_clear_sample_dimension_groups(self):
        '''Remove the netCDF dimension group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for removing the group structure is to
    set the netCDF dimension name, with `nc_set_sample_dimension`,
    with no ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_sample_dimension_groups`,
                 `nc_set_sample_dimension_groups`

    :Returns:

        `tuple` of `str`
            The removed group structure.

    **Examples:**

    >>> f.nc_set_sample_dimension('element')
    >>> f.nc_sample_dimension_groups()
    ()
    >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    '/forecast/model/element'
    >>> f.nc_clear_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_get_sample_dimension()
    'element'

    >>> f.nc_set_sample_dimension('/forecast/model/element')
    >>> f.nc_sample_dimension_groups()
    ('forecast', 'model')
    >>> f.nc_del_sample_dimension('/forecast/model/element')
    '/forecast/model/element'
    >>> f.nc_sample_dimension_groups()
    ()

        '''
        return self._nc_clear_groups(
            nc_get=self.nc_get_sample_dimension,
            nc_set=self.nc_set_sample_dimension,
            nc_groups=self.nc_sample_dimension_groups)


# --- End: class


class NetCDFGlobalAttributes(NetCDF):
    '''Mixin class for accessing netCDF global attributes.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `write`, `nc_clear_global_attributes`,
                 `nc_set_global_attribute`, `nc_set_global_attributes`

    :Parameters:

        values: `bool`, optional
            Return the value (rather than `None`) for any global
            attribute that has, by definition, the same value as a
            construct property.

            .. versionadded:: (cfdm) 1.8.2

    :Returns:

        `dict`
            The selection of properties requested for writing to
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

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `write`, `nc_global_attributes`,
                 `nc_set_global_attribute`, `nc_set_global_attributes`

    :Returns:

        `dict`
            The removed selection of properties requested for writing
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

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.10

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


class NetCDFGroupAttributes(NetCDF):
    '''Mixin class for accessing netCDF group attributes.

    .. versionadded:: (cfdm) 1.8.6

    '''
    def nc_group_attributes(self, values=False):
        '''Return the selection of properties to be written as netCDF group
    attributes.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `write`, `nc_clear_group_attributes`,
                 `nc_set_group_attribute`, `nc_set_group_attributes`

    :Parameters:

        values: `bool`, optional
            Return the value (rather than `None`) for any group
            attribute that has, by definition, the same value as a
            construct property.

    :Returns:

        `dict`
            The selection of properties requested for writing to
            netCDF group attributes.

    **Examples:**

    >>> f.nc_group_attributes()
    {'comment': None}
    >>> f.nc_set_group_attribute('foo')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': None}
    >>> f.nc_set_group_attribute('foo', 'bar')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes(values=True)
    {'comment': 'forecast comment', 'foo': 'bar'}
    >>> f.nc_clear_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('group_attributes')

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

    def nc_clear_group_attributes(self):
        '''Remove the selection of properties to be written as netCDF group
    attributes.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `write`, `nc_group_attributes`,
                 `nc_set_group_attribute`, `nc_set_group_attributes`

    :Returns:

        `dict`
            The removed selection of properties requested for writing
            to netCDF group attributes.

    **Examples:**

    >>> f.nc_group_attributes()
    {'comment': None}
    >>> f.nc_set_group_attribute('foo')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': None}
    >>> f.nc_set_group_attribute('foo', 'bar')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes(values=True)
    {'comment': 'forecast comment', 'foo': 'bar'}
    >>> f.nc_clear_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('group_attributes')

        if out is None:
            out = {}

        self._get_component('netcdf')['group_attributes'] = {}

        return out

    def nc_set_group_attribute(self, prop, value=None):
        '''Select a property to be written as a netCDF group attribute.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `write`, `nc_group_attributes`,
                 `nc_clear_group_attributes`,
                 `nc_set_group_attributes`

    :Parameters:

        prop: `str`
            Select the property to be written (if possible) as a
            netCDF group attribute.

        value: optional
            The value of the netCDF group attribute, which will be
            created (if possible) in addition to the property as
            written to a netCDF data variable. If unset (or `None`)
            then this acts as an instruction to write the property (if
            possible) to a netCDF group attribute instead of to a
            netCDF data variable.

    :Returns:

        `None`

    **Examples:**

    >>> f.nc_group_attributes()
    {'comment': None}
    >>> f.nc_set_group_attribute('foo')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': None}
    >>> f.nc_set_group_attribute('foo', 'bar')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes(values=True)
    {'comment': 'forecast comment', 'foo': 'bar'}
    >>> f.nc_clear_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes()
    {}

        '''
        out = self._get_component('netcdf').get('group_attributes')

        if out is None:
            out = {}

        out[prop] = value

        self._get_component('netcdf')['group_attributes'] = out

    def nc_set_group_attributes(self, properties, copy=True):
        '''Set properties to be written as netCDF group attributes.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `write`, `nc_clear_group_attributes`,
                 `nc_group_attributes`, `nc_set_group_attribute`

    :Parameters:

        properties: `dict`
            Set the properties be written as a netCDF group attribute
            from the dictionary supplied. The value of a netCDF group
            attribute, which will be created (if possible) in addition
            to the property as written to a netCDF data variable. If a
            value of `None` is used then this acts as an instruction
            to write the property (if possible) to a netCDF group
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

    >>> f.nc_group_attributes()
    {'comment': None}
    >>> f.nc_set_group_attribute('foo')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': None}
    >>> f.nc_set_group_attribute('foo', 'bar')
    >>> f.nc_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes(values=True)
    {'comment': 'forecast comment', 'foo': 'bar'}
    >>> f.nc_clear_group_attributes()
    {'comment': None, 'foo': 'bar'}
    >>> f.nc_group_attributes()
    {}

        '''
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        out = self._get_component('netcdf').get('group_attributes')
        if out is None:
            out = {}

        out.update(properties)

        self._get_component('netcdf')['group_attributes'] = out

# --- End: class


class NetCDFUnlimitedDimensions(NetCDF):
    '''Mixin class for accessing netCDF unlimited dimensions.

    .. versionadded:: (cfdm) 1.7.0

    Deprecated at version 1.7.4

    '''
    def nc_unlimited_dimensions(self):
        '''Return the selection of domain axis constructs to be written as
    netCDF unlimited dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: (cfdm) 1.7.0

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
            "Field.nc_unlimited_dimensions was deprecated at version 1.7.4 "
            "and is no longer available. Use DomainAxis.nc_is_unlimited "
            "instead")

    def nc_set_unlimited_dimensions(self, axes):
        '''Select domain axis constructs to be written as netCDF unlimited
    dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: (cfdm) 1.7.0

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
            "Field.nc_set_unlimited_dimensions was deprecated at version "
            "1.7.4 and is no longer available. "
            "Use DomainAxis.nc_set_unlimited instead")

    def nc_clear_unlimited_dimensions(self):
        '''Remove the selection of domain axis constructs to be written as
    netCDF unlimited dimensions.

    By default output netCDF dimensions are not unlimited.

    .. versionadded:: (cfdm) 1.7.0

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
            "Field.nc_clear_unlimited_dimensions was deprecated at version "
            "1.7.4 and is no longer available. "
            "Use DomainAxis.nc_set_unlimited instead.")

# --- End: class


class NetCDFExternal(NetCDF):
    '''Mixin class for accessing the netCDF external variable status.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def nc_get_external(self):
        '''Whether the construct corresponds to an external netCDF variable.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

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


class NetCDFGeometry(NetCDF,
                     _NetCDFGroupsMixin):
    '''Mixin class for accessing the netCDF geometry container variable
    name.

    .. versionadded:: (cfdm) 1.8.0

    '''
    def nc_del_geometry_variable(self, default=ValueError()):
        '''Remove the netCDF geometry container variable name.

    .. versionadded:: (cfdm) 1.8.0

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

    .. versionadded:: (cfdm) 1.8.0

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

    .. versionadded:: (cfdm) 1.8.0

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

    If there are any ``/`` (slash) characters in the netCDF name then
    these act as delimiters for a group hierarchy. By default, or if
    the name starts with a ``/`` character and contains no others, the
    name is assumed to be in the root group.

    .. versionadded:: (cfdm) 1.8.0

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
        if not value or value == '/':
            raise ValueError(
                "Invalid netCDF geometry variable name: {!r}".format(value))

        if '/' in value:
            if not value.startswith('/'):
                raise ValueError(
                    "A netCDF geometry variable name with a group structure "
                    "must start with a '/'. Got {!r}".format(value)
                )

            if value.count('/') == 1:
                value = value[1:]
            elif value.endswith('/'):
                raise ValueError(
                    "A netCDF geometry variable name with a group structure "
                    "can't end with a '/'. Got {!r}".format(value)
                )
        # --- End: if

        self._get_component('netcdf')['geometry_variable'] = value

    def nc_geometry_variable_groups(self):
        '''Return the netCDF geometry variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_geometry_variable_groups`,
    `nc_set_geometry_variable_groups`

    :Returns:

        `tuple` of `str`
            The group structure.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry1')
    >>> f.nc_geometry_variable_groups()
    ()
    >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    '/forecast/model/geometry1'
    >>> f.nc_clear_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    'geometry1'

    >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
    >>> f.nc_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
    '/forecast/model/geometry1'
    >>> f.nc_geometry_variable_groups()
    ()

        '''
        return self._nc_groups(nc_get=self.nc_get_geometry_variable)

    def nc_set_geometry_variable_groups(self, groups):
        '''Set the netCDF geometry variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for setting the group structure is to set
    the netCDF variable name, with `nc_set_geometry_variable`, with
    the group structure delimited by ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_clear_geometry_variable_groups`,
                 `nc_geometry_variable_groups`

    :Parameters:

        groups: sequence of `str`
            The new group structure.

    :Returns:

        `tuple` of `str`
            The group structure prior to being reset.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry1')
    >>> f.nc_geometry_variable_groups()
    ()
    >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    '/forecast/model/geometry1'
    >>> f.nc_clear_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    'geometry1'

    >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
    >>> f.nc_geometry__variablegroups()
    ('forecast', 'model')
    >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
    '/forecast/model/geometry1'
    >>> f.nc_geometry_variable_groups()
    ()

        '''
        return self._nc_set_groups(groups,
                                   nc_get=self.nc_get_geometry_variable,
                                   nc_set=self.nc_set_geometry_variable,
                                   nc_groups=self.nc_geometry_variable_groups)

    def nc_clear_geometry_variable_groups(self):
        '''Remove the netCDF geometry variable group hierarchy.

    The group hierarchy is defined by the netCDF name. Groups are
    delimited by ``/`` (slash) characters in the netCDF name. The
    groups are returned, in hierarchical order, as a sequence of
    strings. If the name is not set, or contains no ``/`` characters
    then an empty sequence is returned, signifying the root group.

    An alternative technique for removing the group structure is to
    set the netCDF variable name, with `nc_set_geometry_variable`,
    with no ``/`` characters.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `nc_geometry_variable_groups`,
                 `nc_set_geometry_variable_groups`

    :Returns:

        `tuple` of `str`
            The removed group structure.

    **Examples:**

    >>> f.nc_set_geometry_variable('geometry1')
    >>> f.nc_geometry_variable_groups()
    ()
    >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
    >>> ()
    >>> f.nc_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    '/forecast/model/geometry1'
    >>> f.nc_clear_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_get_geometry_variable()
    'geometry1'

    >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
    >>> f.nc_geometry_variable_groups()
    ('forecast', 'model')
    >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
    '/forecast/model/geometry1'
    >>> f.nc_geometry_variable_groups()
    ()

        '''
        return self._nc_clear_groups(
            nc_get=self.nc_get_geometry_variable,
            nc_set=self.nc_set_geometry_variable,
            nc_groups=self.nc_geometry_variable_groups)

# --- End: class


class NetCDFHDF5(NetCDF):
    '''Mixin class for accessing the netCDF HDF5 chunksizes.

    .. versionadded:: (cfdm) 1.7.2

    '''
    def nc_hdf5_chunksizes(self):
        '''Return the HDF5 chunksizes for the data.

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: (cfdm) 1.7.2

    .. seealso:: `nc_clear_hdf5_chunksizes`, `nc_set_hdf5_chunksizes`

    :Returns:

        `tuple`
            The current chunksizes.

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
        '''Clear the HDF5 chunksizes for the data.

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: (cfdm) 1.7.2

    .. seealso:: `nc_hdf5_chunksizes`, `nc_set_hdf5_chunksizes`

    :Returns:

        `tuple`
            The chunksizes defined prior to being cleared.

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
        '''Set the HDF5 chunksizes for the data.

    .. note:: Chunksizes are cleared from the output of methods that
              change the data shape.

    .. note:: Chunksizes are ignored for netCDF3 files that do not use
              HDF5.

    .. versionadded:: (cfdm) 1.7.2

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


class NetCDFUnlimitedDimension(NetCDF):
    '''Mixin class for accessing a netCDF unlimited dimension.

    .. versionadded:: (cfdm) 1.7.4

    '''
    def nc_is_unlimited(self):
        '''Inspect the unlimited status of the a netCDF dimension.

    By default output netCDF dimensions are not unlimited. The status
    is used by the `write` function.

    .. versionadded:: (cfdm) 1.7.4

    .. seealso:: `nc_set_unlimited`

    :Returns:

        `bool`
            The existing unlimited status. True and False signify
            "unlimited" and "not unlimited" respectively.

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

    .. versionadded:: (cfdm) 1.7.4

    .. seealso:: `nc_is_unlimited`

    :Parameters:

        value: `bool`
            The new unlimited status. True and False signify
            "unlimited" and "not unlimited" respectively.

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
