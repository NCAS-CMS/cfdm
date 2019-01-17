from builtins import object


class NetCDF(object):
    '''Mixin class for storing simple netCDF elements.

.. versionadded:: 1.7.0

    '''
    def _initialise_netcdf(self, source=None):
        '''Call this from inside the __init__ method of a class that inherits
from this mixin class.

:Parameters:

    source: optional

:Returns:

    `None`

        '''
        if source is None:
             netcdf = {}
        else:        
            try:
                netcdf = source._get_component('netcdf', None).copy()
            except AttributeError:
                netcdf = {}
        #--- End: if
        
        self._set_component('netcdf', netcdf, copy=False)
    #--- End: def

#--- End: class


class NetCDFDimension(NetCDF):
    '''Mixin class for accessing the netCDF dimension name.

.. versionadded:: 1.7.0

    '''
    def nc_del_dimension(self, *default):
        '''Remove the netCDF dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_get_dimension`, `nc_has_dimension`,
             `nc_set_dimension`

:Parameters:

    default: optional
        Return *default* if the netCDF dimension name has not been
        set.

:Returns:

    `str`
        The removed netCDF dimension name. If unset then *default* is
        returned, if provided.

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
            return self._get_component('netcdf').pop('dimension', *default)
        except KeyError:
            raise AttributeError(
                "{!r} object has no netCDF dimension name".format(
                    self.__class__.__name__))
    #--- End: def

    def nc_get_dimension(self, *default):
        '''Return the netCDF dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_dimension`, `nc_has_dimension`,
             `nc_set_dimension`

:Parameters:

    default: optional
        Return *default* if the netCDF dimension name has not been
        set.

:Returns:

    `str`
        The netCDF dimension name. If unset then *default* is
        returned, if provided.

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
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_dimension(self):
        '''Whether the netCDF dimension name has been set.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_dimension`, `nc_get_dimension`,
             `nc_set_dimension`

:Returns:

    `bool`
        True if the netCDF dimension name has been set, otherwise
        False.

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
    #--- End: def

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
    #--- End: def

#--- End: class


class NetCDFVariable(NetCDF):
    '''Mixin class for accessing the netCDF variable name.

.. versionadded:: 1.7.0

    '''
    def nc_del_variable(self, *default):
        '''Remove the netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `nc_get_variable`, `nc_has_variable`, `nc_set_variable`

:Parameters:

    default: optional
        Return *default* if the netCDF variable name has not been set.

:Returns:

    `str`
        The removed netCDF variable name. If unset then *default* is
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
            return self._get_component('netcdf').pop('variable', *default)
        except KeyError:
            raise AttributeError(
                "{!r} object has no netCDF variable name".format(
                    self.__class__.__name__))
    #--- End: def
        
    def nc_get_variable(self, *default):
        '''Return the netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_variable`, `nc_has_variable`, `nc_set_variable`

:Parameters:

    default: optional
        Return *default* if the netCDF variable name has not been set.

:Returns:

    `str`
        The netCDF variable name. If unset then *default* is returned,
        if provided.

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
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF variable name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_variable(self):
        '''Whether the netCDF variable name has been set.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_variable`, `nc_get_variable`, `nc_set_variable`

:Returns:

    `bool`
        True if the netCDF variable name has been set, otherwise
        False.

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
    #--- End: def

    def nc_set_variable(self, value):
        '''Set the netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_variable`, `nc_get_variable`, `nc_has_variable`

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
    #--- End: def

#--- End: class


class NetCDFSampleDimension(NetCDF):
    '''Mixin class for accessing the netCDF sample dimension name.

.. versionadded:: 1.7.0

    '''
    def nc_del_sample_dimension(self, *default):
        '''Remove the netCDF sample dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_get_sample_dimension`, `nc_has_sample_dimension`,
             `nc_set_sample_dimension`

:Parameters:

    default: optional        
        Return *default* if the netCDF sample dimension name has not
        been set.

:Returns:

    `str`
        The removed netCDF sample dimension name. If unset then
        *default* is returned, if provided.

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
            return self._get_component('netcdf').pop('sample_dimension', *default)
        except KeyError:
            raise AttributeError("{!r} has no netCDF sample dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_get_sample_dimension(self, *default):
        '''Return the netCDF sample dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_sample_dimension`, `nc_has_sample_dimension`,
             `nc_set_sample_dimension`

:Parameters:

    default: optional        
        Return *default* if the netCDF sample dimension name has not
        been set.

:Returns:

    `str`
        The netCDF sample dimension name. If unset then *default* is
        returned, if provided.

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
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF sample dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_sample_dimension(self):
        '''Whether the netCDF sample dimension name has been set.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_sample_dimension`, `nc_get_sample_dimension`,
             `nc_set_sample_dimension`

:Returns:
     
    `bool`
        True if the netCDF sample dimension name has been set,
        otherwise False.

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
    #--- End: def

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
    #--- End: def

#--- End: class

class NetCDFInstanceDimension(NetCDF):
    '''Mixin class for accessing the netCDF instance dimension name.

.. versionadded:: 1.7.0

    '''
    def nc_del_instance_dimension(self,*default):
        '''Return the netCDF instance dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_instance_dimension`, `nc_has_instance_dimension`,
             `nc_set_instance_dimension`

:Parameters:

    default: optional        
        Return *default* if the netCDF instance dimension name has not
        been set.

:Returns:

    `str`
        The netCDF instance dimension name. If unset then *default* is
        returned, if provided.

**Examples:**

>>> f.nc_set_instance_dimension('time')
>>> f.nc_has_instance_dimension()
True
>>> f.nc_get_instance_dimension()
'time'
>>> f.nc_del_instance_dimension()
'time'
>>> f.nc_has_instance_dimension()
False
>>> print(f.nc_get_instance_dimension(None))
None
>>> print(f.nc_del_instance_dimension(None))
None
 
        '''        
        try:
            return self._get_component('netcdf').pop('instance_dimension', *default)
        except KeyError:
            raise AttributeError("{!r} has no netCDF instance dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_get_instance_dimension(self, *default):
        '''Return the netCDF instance dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_instance_dimension`, `nc_has_instance_dimension`,
             `nc_set_instance_dimension`

:Parameters:

    default: optional        
        Return *default* if the netCDF instance dimension name has not
        been set.

:Returns:

    `str`
        The netCDF instance dimension name. If unset then *default* is
        returned, if provided.

**Examples:**

>>> f.nc_set_instance_dimension('time')
>>> f.nc_has_instance_dimension()
True
>>> f.nc_get_instance_dimension()
'time'
>>> f.nc_del_instance_dimension()
'time'
>>> f.nc_has_instance_dimension()
False
>>> print(f.nc_get_instance_dimension(None))
None
>>> print(f.nc_del_instance_dimension(None))
None
        '''
        try:
            return self._get_component('netcdf')['instance_dimension']
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF instance dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_instance_dimension(self):
        '''Whether the netCDF instance dimension name has been set.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_instance_dimension`, `nc_get_instance_dimension`,
             `nc_set_instance_dimension`

:Returns:
     
    `bool`
        True if the netCDF instance dimension name has been set,
        otherwise False.

**Examples:**

>>> f.nc_set_instance_dimension('time')
>>> f.nc_has_instance_dimension()
True
>>> f.nc_get_instance_dimension()
'time'
>>> f.nc_del_instance_dimension()
'time'
>>> f.nc_has_instance_dimension()
False
>>> print(f.nc_get_instance_dimension(None))
None
>>> print(f.nc_del_instance_dimension(None))
None 
        '''
        return 'instance_dimension' in self._get_component('netcdf')
    #--- End: def

    def nc_set_instance_dimension(self, value):
        '''Set the netCDF instance dimension name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_instance_dimension`, `nc_get_instance_dimension`,
             `nc_has_instance_dimension`
             
:Parameters:

    value: `str`
        The value for the netCDF instance dimension name.

:Returns:

    `None`

**Examples:**

>>> f.nc_set_instance_dimension('time')
>>> f.nc_has_instance_dimension()
True
>>> f.nc_get_instance_dimension()
'time'
>>> f.nc_del_instance_dimension()
'time'
>>> f.nc_has_instance_dimension()
False
>>> print(f.nc_get_instance_dimension(None))
None
>>> print(f.nc_del_instance_dimension(None))
None
 
        '''
        self._get_component('netcdf')['instance_dimension'] = value
    #--- End: def

#--- End: class


class NetCDFDataVariable(NetCDF):
    '''Mixin class for accessing netCDF elements relating to a data
variable.

.. versionadded:: 1.7.0

    '''
    def nc_global_attributes(self, attributes=None):
        '''Return or replace the selection of properties to be written as
netCDF global attributes.

When multiple field constructs are being written to the same file, it
is not possible to create a netCDF global attribute from a property
that has different values for different fields being written. In this
case the property will not be written as a netCDF global attribute,
even if it has been selected as such by this method, but will appear
instead as an attribute on the netCDF data variable corresponding to
the field construct.

The `description of file contents
<http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#description-of-file-contents>`_
properties are always written as netCDF global attributes, if
possible, so selecting them is optional.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_unlimited_dimensions`

:Parameters:

    attributes: sequence of `str`, optional   
        Replace the exisiting selection of properties to be written
        out as netCDF global attributes.

        *Parameter example:*
          ``attributes=['project']``
        
        *Parameter example:*
          ``attributes=()``        

:Returns:

    `set`
        The selection of domain axis constructs prior to being
        changed, or the current selection if no changes were
        specified.

**Examples:**

>>> x = f.nc_global_attributes(['Conventions', 'project'])
>>> f.nc_global_attributes()
{'Conventions', 'project'}
>>> f.nc_global_attributes([])
{'Conventions', 'project'}
>>> f.nc_global_attributes()
set()

        '''
        out = self._get_component('netcdf').get('global_attributes')
        
        if out is None:
            out = set()

        if attributes:
            self._get_component('netcdf')['global_attributes'] = tuple(attributes)

        return set(out)
    #--- End: def
    
    def nc_unlimited_dimensions(self, axes=None):
        '''Return or replace the selection of domain axis constructs to be
written as netCDF unlimited dimensions.

By default output netCDF dimensions are not unlimited.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_global_attributes`

:Parameters:

    axes: sequence of `str`, optional   
        Replace the exisiting selection of domain axis constructs to
        be written out as netCDF unlimited dimensions. Domain axis
        constructs are identified by their construct identifiers.

        *Parameter example:*
          ``axes=['domainaxis0', 'domainaxis1']``
        
        *Parameter example:*
          ``axes=()``        

:Returns:

    `set`
        The selection of domain axis construct identifiers prior to
        being changed, or the current selection if no changes were
        specified.

**Examples:**

>>> x = f.nc_unlimited_dimensions(['domainaxis1'])
>>> f.nc_unlimited_dimensions()
{'domainaxis1'}
>>> f.nc_unlimited_dimensions([])
{'domainaxis1'}
>>> f.nc_unlimited_dimensions()
set()

        '''
        out = self._get_component('netcdf').get('unlimited_dimensions')

        if out is None:
            out = set()

        if axes:
            self._get_component('netcdf')['unlimited_dimensions'] = tuple(axes)

        return set(out)
#--- End: def


class NetCDFExternal(NetCDF):
    '''Mixin class for accessing the netCDF external variable status.

.. versionadded:: 1.7.0

    '''
    def nc_external(self, *external):
        '''Whether the construct correponds to an external netCDF variable.

.. versionadded:: 1.7.0

:Parameters:

    external: `bool`, optional
        Set the external status. If True then the construct will be
        written to a netCDF extenal file, if specified during the
        write process.

:Returns:

    `bool`
        The external status or, if the *external* parameter was set,
        the original status.

**Examples:**

>>> c.nc_external()
False
>>> c.nc_external(True)
False
>>> c.nc_external()
True

        '''
        old =  self._get_component('netcdf').get('external', False)
        if external:
            self._get_component('netcdf')['external'] = bool(external[0])

        return old
    #--- End: def

#--- End: class
