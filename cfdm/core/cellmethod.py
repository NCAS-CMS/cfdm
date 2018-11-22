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

.. versionadded:: 1.7
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

#    def __repr__(self):
#        '''x.__repr__() <==> repr(x)
#
#        '''
#        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
#    #--- End: def
#
#    def __str__(self):
#        '''x.__str__() <==> str(x)
#
#Return a CF-netCDF-like string of the cell method.
#
#Note that if the intention is to use this string in a CF-netCDF
#cell_methods attribute then, unless they are standard names, the axes
#names will need to be modified to be netCDF dimension names.
#
#        '''     
#        string = ['{0}:'.format(axis) for axis in self.get_axes(())]
#
#        string.append(self.get_property('method', ''))
#
#        for portion in ('within', 'where', 'over'):
#            p = self.get_property(portion, None)
#            if p is not None:
#                string.extend((portion, p))
#        #--- End: for
#
#        intervals = self.get_property('intervals', ())
#        comment   = self.get_property('comment', None)
#
#        if intervals:
#            x = ['(']
#
#            y = ['interval: {0}'.format(data) for data in intervals]
#            x.append(' '.join(y))
#
#            if comment is not None:
#                x.append(' comment: {0}'.format(comment))
#
#            x.append(')')
#
#            string.append(''.join(x))
#
#        elif comment is not None:
#            string.append('({0})'.format(comment))
#
#        return ' '.join(string)
#    #--- End: def

    @property
    def construct_type(self):
        '''Return a description of the construct type.
        
.. versionadded:: 1.7
        
:Returns:

    out: `str`
        The construct type.

        '''
        return 'cell_method'

    def del_axes(self, *default):
        '''Remove the axes of the cell method.

.. versionadded:: 1.7

.. seealso:: `get_axes`, `has_axes`, `set_axes`

:Parameters:

    default: optional
        Return *default* if axes have not been set.

:Returns:

     out:
        The removed axes, identified by field key or standard name. If
        unset then *default* is returned, if provided.

**Examples**

>>> c.set_axes('area')
>>> print c.del_axes()
('area',)
>>> print f.del_axes()
None

        '''
        return self._del_component('axes')
    #--- End: def
    
    def get_axes(self, *default):
        '''Return the axes of the cell method.

.. versionadded:: 1.7

.. seealso:: `del_axes`, `has_axes`, `set_axes`

:Parameters:

    default: optional
        Return *default* if and only if axes have not been set.

:Returns:

    out: `tuple`
        The axes. If axes have not been set then return the value
        of *default* parameter, if provided.

**Examples**

>>> c.set_axes(['time'])
>>> c.get_axes()
('time',)
>>> c.del_axes()
>>> c.get_axes()
AttributeError: 'CellMethod' object has no component 'axes'
>>> c.get_axes('NO AXES')
'NO AXES'

        '''
        return self._get_component('axes', *default)
    #--- End: def

    def has_axes(self):
        '''Whether the axes of the cell method have been set.

.. versionadded:: 1.7

.. seealso:: `del_axes`, `get_axes`, `set_axes`

:Examples 1:

>>> x = c.has_axes()

:Returns:

     out: `bool`
        True if the axes have been set, otherwise False.

**Examples**

>>> if c.has_axes():
...     print 'Has axes'

'''
        return self._has_component('axes')
    #--- End: def

    def set_axes(self, value, copy=True):
        '''Set the axes of the cell method.

.. versionadded:: 1.7

.. seealso:: `del_axes`, `get_axes`, `has_axes`

:Examples 1:

>>> c.set_axes('time')

:Parameters:

    value: (sequence of) `str`
        The value for the axes.

:Returns:

     `None`

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
