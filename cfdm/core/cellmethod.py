from builtins import (str, super)
from past.builtins import basestring

from copy import deepcopy

from . import abstract


class CellMethod(abstract.Properties):
    '''A cell method construct of the CF data model.

One or more cell method constructs describe how the cell values of the
field construct represent the variation of the physical quantity
within its cells, i.e. the structure of the data at a higher
resolution.

A single cell method construct consists of a set of axes, a "method"
property which describes how a value of the field construct's data
array describes the variation of the quantity within a cell over those
axes (e.g. a value might represent the cell area average), and
properties serving to indicate more precisely how the method was
applied (e.g. recording the spacing of the original data, or the fact
that the method was applied only over El Nino years).

.. versionadded:: 1.7.0

    '''
    def __init__(self, axes=None, properties=None, source=None,
                 copy=True):
        '''**Initialisation**

:Parameters:

    axes: sequence of `str`, optional
        Set the axes of the cell method construct. Either one or more
        domain axis construct identifiers or standard names. Ignored
        if the *source* parameter is set.

          *Example:*
             ``axes=['domainaxis0']``
        
          *Example:*
             ``axes=('domainaxis0', 'domainaxis1')``
        
          *Example:*
             ``axes=('area',)``
        
          *Example:*
             ``axes=['domainaxis2', 'time']``
        
         The axes may also be set after initialisation with the
         `set_axes` method.

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Example:*
          ``properties={'method': 'variance'}``
       
        *Example:*
          ``properties={'method': 'mean', 'where': 'sea'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    source: optional
        Initialize the axes and properties from those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization By default parameters are deep copied.

        '''
        super().__init__(properties=properties, source=source,
                         copy=copy)

        if source:
            try:
                axes = source.get_axes(None)
            except AttributeErrror:
                axes = None              
        #--- End: if

        if axes is not None:                
            axes = self.set_axes(axes)
    #--- End: def

    @property
    def construct_type(self):
        '''Return a description of the construct type.
        
.. versionadded:: 1.7.0
        
:Returns:

    `str`
        The construct type.

        '''
        return 'cell_method'

    def del_axes(self, *default):
        '''Remove the axes of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `get_axes`, `has_axes`, `set_axes`

:Parameters:

    default: optional
        Return *default* if axes have not been set.

:Returns:

    `tuple` or *default*
        The removed axes, identified by field key or standard name. If
        unset then *default* is returned, if provided.

**Examples:**

>>> c.set_axes(['domainaxis1'])
>>> c.has_axes()
True
>>> c.get_axes()
('time',)
>>> c.del_axes()
>>> c.has_axes()
False
>>> c.get_axes('NO AXES')
'NO AXES'
>>> c.del_axes('NO AXES')
'NO AXES'

        '''
        return self._del_component('axes')
    #--- End: def
    
    def get_axes(self, *default):
        '''Return the axes of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_axes`, `has_axes`, `set_axes`

:Parameters:

    default: optional
        Return *default* if axes have not been set.

:Returns:

    `tuple`
        The axes. If axes have not been set then return the value
        of *default* parameter, if provided.

**Examples:**

>>> c.set_axes(['domainaxis1'])
>>> c.has_axes()
True
>>> c.get_axes()
('time',)
>>> c.del_axes()
>>> c.has_axes()
False
>>> c.get_axes('NO AXES')
'NO AXES'
>>> c.del_axes('NO AXES')
'NO AXES'

        '''
        return self._get_component('axes', *default)
    #--- End: def

    def get_method(self, *default):
        '''Return the method of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_method`, `has_method`, `set_method`

:Parameters:

    default: optional
        Return *default* if the "method" propoerty has not been set.

:Returns:

    `tuple`
        The method. If the method has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_method(['domainaxis1'])
>>> c.has_method()
True
>>> c.get_method()
'variance'
>>> c.del_method()
>>> c.has_method()
False
>>> c.get_method('NO METHOD')
'NO METHOD'
>>> c.del_method('NO METHOD')
'NO METHOD'

        '''
        return self._get_component('method', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default* if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default* if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default*  if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default*  if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default*  if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default* if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default*  if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('<TODO>', *default)
    #--- End: def

    def get_xx(self, *default):
        '''Return the xx of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_xx`, `has_xx`, `set_xx`

:Parameters:

    default: optional
        Return *default*  if the xx have not been set.

:Returns:

    `tuple` or *default*
        The xx. If the xx has not been set then return the
        value of *default* parameter, if provided.

**Examples:**

>>> c.set_xx(<TODO>)
>>> c.has_xx()
True
>>> c.get_xx()
<TODO>
>>> c.del_xx()
>>> c.has_xx()
False
>>> c.get_xx('NO XX')
'NO XX'
>>> c.del_xx('NO XX')
'NO XX'

        '''
        return self._get_component('over', *default)
    #--- End: def

    def get_where(self, *default):
        '''Return the "where" property of the cell method.

The "where" property indicates that the method has been applied to
only a portion of a cell.

.. versionadded:: 1.7.0

.. seealso:: `del_where`, `has_where`, `set_where`

:Parameters:

    default: optional
        Return *default* if the "where" property has not been set.

:Returns:

    `str`
        The where property. If the where property has not been set
        then return the value of *default* parameter, if provided.

**Examples:**

>>> c.set_where('sea')
>>> c.has_where()
True
>>> c.get_where()
'sea'
>>> c.del_where()
>>> c.has_where()
False
>>> c.get_where('NO WHERE')
'NO WHERE'
>>> c.del_where('NO WHERE')
'NO WHERE'

        '''
        return self._get_component('where', *default)
    #--- End: def

    def has_axes(self):
        '''Whether the axes of the cell method have been set.

.. versionadded:: 1.7.0

.. seealso:: `del_axes`, `get_axes`, `set_axes`

:Returns:

     `bool`
        True if the axes have been set, otherwise False.

**Examples:**

>>> c.set_axes(['domainaxis1'])
>>> c.has_axes()
True
>>> c.get_axes()
('time',)
>>> c.del_axes()
>>> c.has_axes()
False
>>> c.get_axes('NO AXES')
'NO AXES'
>>> c.del_axes('NO AXES')
'NO AXES'

'''
        return self._has_component('axes')
    #--- End: def

    def set_axes(self, value, copy=True):
        '''Set the axes of the cell method.

.. versionadded:: 1.7.0

.. seealso:: `del_axes`, `get_axes`, `has_axes`

:Parameters:

    value: (sequence of) `str`
        The axes, specified either by the construct identifiers of
        domain axis constructs; standard names; or the special string
        ``'area'``.

        *Example:*
          ``axes='domainaxis0'``

        *Example:*
          ``axes='time'``

        *Example:*
          ``axes='area'``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis2']``

        *Example:*
          ``axes=['time', 'area']``

        *Example:*
          ``axes=['domainaxis0', 'time']``

:Returns:

     `None`

**Examples:**

>>> c.set_axes(['domainaxis1'])
>>> c.has_axes()
True
>>> c.get_axes()
('time',)
>>> c.del_axes()
>>> c.has_axes()
False
>>> c.get_axes('NO AXES')
'NO AXES'
>>> c.del_axes('NO AXES')
'NO AXES'

>>> c.set_axes(['domainaxis1', 'domainaxis0'])

>>> c.set_axes(['time', 'domainaxis0'])

>>> c.set_axes('time')

        '''
        if copy:
            value = deepcopy(value)
        
        if isinstance(value, basestring):
            value = (value,)
        else:
            value = tuple(value)
            
        return self._set_component('axes', value, copy=False)
    #--- End: def

#--- End: class
