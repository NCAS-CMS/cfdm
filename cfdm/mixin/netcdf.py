from builtins import object

from copy import deepcopy


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
                netcdf = deepcopy(source._get_component('netcdf', {}))
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
            return self._default(default,
                   "{!r} has no netCDF dimension name".format(
                       self.__class__.__name__))
    #--- End: def

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
            return self._default(default,
                   "{!r} has no netCDF dimension name".format(
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
    def nc_del_variable(self, default=ValueError()):
        '''Remove the netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `nc_get_variable`, `nc_has_variable`, `nc_set_variable`

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
            return self._default(default,
                   "{!r} has no netCDF variable name".format(
                       self.__class__.__name__))
    #--- End: def
        
    def nc_get_variable(self, default=ValueError()):
        '''Return the netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `nc_del_variable`, `nc_has_variable`, `nc_set_variable`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the netCDF
        variable name has not been set. If set to an `Exception`
        instance then it will be raised instead.

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
            return self._default(default,
                   "{!r} has no netCDF variable name".format(
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
            return self._default(default,
                   "{!r} has no netCDF sample dimension name".format(
                       self.__class__.__name__))
    #--- End: def

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
            return self._default(default,
                   "{!r} has no netCDF sample dimension name".format(
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


#class NetCDFInstanceDimension(NetCDF):
#    '''Mixin class for accessing the netCDF instance dimension name.
#
#.. versionadded:: 1.7.0
#
#    '''
#    def nc_del_instance_dimension(self,default=ValueError()):
#        '''Return the netCDF instance dimension name.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `nc_del_instance_dimension`, `nc_has_instance_dimension`,
#             `nc_set_instance_dimension`
#
#:Parameters:
#
#    default: optional
#        Return the value of the *default* parameter if the netCDF
#        instance dimension name has not been set. If set to an
#        `Exception` instance then it will be raised instead.
#
#:Returns:
#
#    `str`
#        The netCDF instance dimension name.
#
#**Examples:**
#
#>>> f.nc_set_instance_dimension('time')
#>>> f.nc_has_instance_dimension()
#True
#>>> f.nc_get_instance_dimension()
#'time'
#>>> f.nc_del_instance_dimension()
#'time'
#>>> f.nc_has_instance_dimension()
#False
#>>> print(f.nc_get_instance_dimension(None))
#None
#>>> print(f.nc_del_instance_dimension(None))
#None
# 
#        '''
#        try:
#            return self._get_component('netcdf').pop('instance_dimension')
#        except KeyError:
#            return self._default(default,
#                   "{!r} has no netCDF instance dimension name".format(
#                       self.__class__.__name__))
#    #--- End: def
#
#    def nc_get_instance_dimension(self, default=ValueError()):
#        '''Return the netCDF instance dimension name.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `nc_del_instance_dimension`, `nc_has_instance_dimension`,
#             `nc_set_instance_dimension`
#
#:Parameters:
#
#    default: optional
#        Return the value of the *default* parameter if the netCDF
#        instance dimension name has not been set. If set to an
#        `Exception` instance then it will be raised instead.
#
#:Returns:
#
#    `str`
#        The netCDF instance dimension name.
#
#**Examples:**
#
#>>> f.nc_set_instance_dimension('time')
#>>> f.nc_has_instance_dimension()
#True
#>>> f.nc_get_instance_dimension()
#'time'
#>>> f.nc_del_instance_dimension()
#'time'
#>>> f.nc_has_instance_dimension()
#False
#>>> print(f.nc_get_instance_dimension(None))
#None
#>>> print(f.nc_del_instance_dimension(None))
#None
#
#        '''
#        try:
#            return self._get_component('netcdf')['instance_dimension']
#        except KeyError:
#            return self._default(default,
#                   "{!r} has no netCDF instance dimension name".format(
#                       self.__class__.__name__))
#    #--- End: def
#
#    def nc_has_instance_dimension(self):
#        '''Whether the netCDF instance dimension name has been set.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `nc_del_instance_dimension`, `nc_get_instance_dimension`,
#             `nc_set_instance_dimension`
#
#:Returns:
#     
#    `bool`
#        True if the netCDF instance dimension name has been set,
#        otherwise False.
#
#**Examples:**
#
#>>> f.nc_set_instance_dimension('time')
#>>> f.nc_has_instance_dimension()
#True
#>>> f.nc_get_instance_dimension()
#'time'
#>>> f.nc_del_instance_dimension()
#'time'
#>>> f.nc_has_instance_dimension()
#False
#>>> print(f.nc_get_instance_dimension(None))
#None
#>>> print(f.nc_del_instance_dimension(None))
#None 
#        '''
#        return 'instance_dimension' in self._get_component('netcdf')
#    #--- End: def
#
#    def nc_set_instance_dimension(self, value):
#        '''Set the netCDF instance dimension name.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `nc_del_instance_dimension`, `nc_get_instance_dimension`,
#             `nc_has_instance_dimension`
#             
#:Parameters:
#
#    value: `str`
#        The value for the netCDF instance dimension name.
#
#:Returns:
#
#    `None`
#
#**Examples:**
#
#>>> f.nc_set_instance_dimension('time')
#>>> f.nc_has_instance_dimension()
#True
#>>> f.nc_get_instance_dimension()
#'time'
#>>> f.nc_del_instance_dimension()
#'time'
#>>> f.nc_has_instance_dimension()
#False
#>>> print(f.nc_get_instance_dimension(None))
#None
#>>> print(f.nc_del_instance_dimension(None))
#None
# 
#        '''
#        self._get_component('netcdf')['instance_dimension'] = value
#    #--- End: def
#
##--- End: class


class NetCDFGlobalAttributes(NetCDF):
    '''Mixin class for accessing netCDF global attributes.

.. versionadded:: 1.7.0

    '''
    def nc_global_attributes(self):
        '''Return the selection of properties to be written as netCDF global
attributes.

When multiple field constructs are being written to the same file, it
is only possible to create a netCDF global attribute from a property
that has identical values for each field construct. If any field
construct's property has a different value then the property will not
be written as a netCDF global attribute, even if it has been selected
as such, but will appear instead as attributes on the netCDF data
variables corresponding to each field construct.

The standard description-of-file-contents properties are always
written as netCDF global attributes, if possible, so selecting them is
optional.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_clear_global_attributes`,
             `nc_set_global_attribute`

:Returns:

    `dict`
        The selection of properties requested for writting to netCDF
        global attributes.

**Examples:**

>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None}
>>> f.nc_set_global_attribute('foo')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None, 'foo'}
>>> f.nc_set_global_attribute('comment', 'global comment')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_clear_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_global_attributes()
{}

        '''
        out = self._get_component('netcdf').get('global_attributes')
        
        if out is None:
            return {}
        
        return out.copy()
    #--- End: def
    
    def nc_clear_global_attributes(self):
        '''Remove the selection of properties to be written as netCDF global
attributes.

When multiple field constructs are being written to the same file, it
is only possible to create a netCDF global attribute from a property
that has identical values for each field construct. If any field
construct's property has a different value then the property will not
be written as a netCDF global attribute, even if it has been selected
as such, but will appear instead as attributes on the netCDF data
variables corresponding to each field construct.

The standard description-of-file-contents properties are always
written as netCDF global attributes, if possible, so selecting them is
optional.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_global_attributes`,
             `nc_set_global_attribute`

:Returns:

    `dict`
        The removed selection of properties requested for writting to
        netCDF global attributes.

**Examples:**

>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None}
>>> f.nc_set_global_attribute('foo')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None, 'foo'}
>>> f.nc_set_global_attribute('comment', 'global comment')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_clear_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_global_attributes()
{}

        '''
        out = self._get_component('netcdf').get('global_attributes')
        
        if out is None:
            out = {}

        self._get_component('netcdf')['global_attributes'] = {}

        return out
    #--- End: def
    
    def nc_set_global_attribute(self, prop, value=None):
        '''Select a property to be written as a netCDF global attribute.

When multiple field constructs are being written to the same file, it
is only possible to create a netCDF global attribute from a property
that has identical values for each field construct. If any field
construct's property has a different value then the property will not
be written as a netCDF global attribute, even if it has been selected
as such, but will appear instead as attributes on the netCDF data
variables corresponding to each field construct.

The standard description-of-file-contents properties are always
written as netCDF global attributes, if possible, so selecting them is
optional.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_global_attributes`,
             `nc_clear_global_attributes`

:Parameters:

    prop: `str`
        Select the property to be written (if possible) as a netCDF
        global attribute.

    value: optional
        The value of the netCDF global attribute, which will be
        created (if possible) in addition to the property as written
        to a netCDF data variable. If unset (or `None`) then this acts
        as an instruction to write the property (if possible) to a
        netCDF global attribute instead of to a netCDF data variable.
        
:Returns:

    `None`

**Examples:**

>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None}
>>> f.nc_set_global_attribute('foo')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': None, 'foo'}
>>> f.nc_set_global_attribute('comment', 'global comment')
>>> f.nc_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_clear_global_attributes()
{'Conventions': None, 'comment': 'global_comment', 'foo'}
>>> f.nc_global_attributes()
{}

        '''
        out = self._get_component('netcdf').get('global_attributes')
        
        if out is None:
            out = {}        

        out[prop] = value
        
        self._get_component('netcdf')['global_attributes'] = out
    #--- End: def
    
#--- End: class


class NetCDFUnlimitedDimensions(NetCDF):
    '''Mixin class for accessing netCDF unlimited dimensions.

.. versionadded:: 1.7.0

    '''
    def nc_unlimited_dimensions(self):
        '''Return the selection of domain axis constructs to be written as
netCDF unlimited dimensions.

By default output netCDF dimensions are not unlimited.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_clear_unlimited_dimensions`,
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
        out = self._get_component('netcdf').get('unlimited_dimensions')
        
        if out is None:
            return set()

        return set(out)
    #--- End: def

    def nc_set_unlimited_dimensions(self, axes):
        '''Select domain axis constructs to be written as netCDF unlimited
dimensions.

By default output netCDF dimensions are not unlimited.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_unlimited_dimensions`,
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
        out = self._get_component('netcdf').get('unlimited_dimensions')
        
        if out is None:
            out = set()
        else:
            out = set(out)

        out.update(axes)
            
        self._get_component('netcdf')['unlimited_dimensions'] = tuple(out)
    #--- End: def

    def nc_clear_unlimited_dimensions(self):
        '''Remove the selection of domain axis constructs to be written as
netCDF unlimited dimensions.

By default output netCDF dimensions are not unlimited.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `nc_unlimited_dimensions`,
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
        out = self._get_component('netcdf').get('unlimited_dimensions')
        
        if out is None:
            out = set()
        else:
            out = set(out)

        self._get_component('netcdf')['unlimited_dimensions'] = ()

        return out
    #--- End: def
    
#--- End: class


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
    #--- End: def

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
    #--- End: def

#--- End: class


class NetCDFGeometry(NetCDF):
    '''Mixin class for accessing the netCDF geometry container variable
name.

.. versionadded:: 1.8.0

    '''   
    def nc_del_geometry(self, default=ValueError()):
        '''Remove the netCDF geometry container variable name.

.. versionadded:: 1.8.0

.. seealso:: `nc_get_geometry`, `nc_has_geometry`, `nc_set_geometry`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the netCDF
        dimension name has not been set. If set to an `Exception`
        instance then it will be raised instead.

:Returns:

    `str`
        The removed netCDF geometry container variable name.

**Examples:**

>>> f.nc_set_geometry('geometry')
>>> f.nc_has_geometry()
True
>>> f.nc_get_geometry()
'geometry'
>>> f.nc_del_geometry()
'geometry'
>>> f.nc_has_geometry()
False
>>> print(f.nc_get_geometry(None))
None
>>> print(f.nc_del_geometry(None))
None

        '''
        try:
            return self._get_component('netcdf').pop('geometry')
        except KeyError:
            return self._default(default,
                   "{!r} has no netCDF geometry name".format(
                       self.__class__.__name__))
    #--- End: def

    def nc_get_geometry(self, default=ValueError()):
        '''Return the netCDF geometry container variable name.

.. versionadded:: 1.8.0

.. seealso:: `nc_del_geometry`, `nc_has_geometry`, `nc_set_geometry`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the netCDF
        dimension name has not been set. If set to an `Exception`
        instance then it will be raised instead.

:Returns:

    `str`
        The netCDF geometry container variable name.

**Examples:**

>>> f.nc_set_geometry('geometry')
>>> f.nc_has_geometry()
True
>>> f.nc_get_geometry()
'geometry'
>>> f.nc_del_geometry()
'geometry'
>>> f.nc_has_geometry()
False
>>> print(f.nc_get_geometry(None))
None
>>> print(f.nc_del_geometry(None))
None

        '''   
        try:
            return self._get_component('netcdf')['geometry']
        except KeyError:
            return self._default(default,
                   "{!r} has no netCDF geometry name".format(
                       self.__class__.__name__))
    #--- End: def

    def nc_has_geometry(self):
        '''Whether the netCDF geometry container variable name has been set.

.. versionadded:: 1.8.0

.. seealso:: `nc_del_geometry`, `nc_get_geometry`, `nc_set_geometry`

:Returns:

    `bool`
        True if the netCDF geometry container variable name has been
        set, otherwise False.

**Examples:**

>>> f.nc_set_geometry('geometry')
>>> f.nc_has_geometry()
True
>>> f.nc_get_geometry()
'geometry'
>>> f.nc_del_geometry()
'geometry'
>>> f.nc_has_geometry()
False
>>> print(f.nc_get_geometry(None))
None
>>> print(f.nc_del_geometry(None))
None

        '''
        return 'geometry' in self._get_component('netcdf')
    #--- End: def

    def nc_set_geometry(self, value):
        '''Set the netCDF geometry container variable name.
        
.. versionadded:: 1.8.0

.. seealso:: `nc_del_geometry`, `nc_get_geometry`, `nc_has_geometry`

:Parameters:

    value: `str`
        The value for the netCDF geometry container variable name.

:Returns:

    `None`

**Examples:**

>>> f.nc_set_geometry('geometry')
>>> f.nc_has_geometry()
True
>>> f.nc_get_geometry()
'geometry'
>>> f.nc_del_geometry()
'geometry'
>>> f.nc_has_geometry()
False
>>> print(f.nc_get_geometry(None))
None
>>> print(f.nc_del_geometry(None))
None

        '''
        self._get_component('netcdf')['geometry'] = value
    #--- End: def

#--- End: class

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
    #--- End: def

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
    #--- End: def

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
        The chunksizes for each dimension. Can be integers from 0 to
        the dimension size.

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
"chunksizes must be a sequence with the same length as dimensions")

            for i, j in zip(chunksizes, shape):
                if i < 0:
                    raise ValueError("chunksize cannot be negative")
                if i > j:
                    raise ValueError("chunksize cannot exceed dimension size")
        #--- End: try
        
        self._get_component('netcdf')['hdf5_chunksizes'] = tuple(chunksizes)
    #--- End: def

#--- End: class
