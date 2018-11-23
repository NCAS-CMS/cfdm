from __future__ import print_function
from builtins import super

import textwrap

import numpy
import sys

from . import Container #, Equals

#from .equals import Equals


class Properties(Container):
    '''Mixin class for descriptive properties.

    '''

    def _dump_properties(self, _prefix='', _level=0,
                         _omit_properties=None):
        '''TODO

.. versionadded:: 1.7

:Parameters:

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    _level: `int`, optional

:Returns:

    out: `str`

**Examples:**

'''
        indent0 = '    ' * _level
        string = []

        properties = self.properties()
        
        if _omit_properties:
            for prop in _omit_properties:
                 properties.pop(prop, None)
        #--- End: if
 
        for prop, value in sorted(properties.items()):
            name   = '{0}{1}{2} = '.format(indent0, _prefix, prop)
            value  = repr(value)
            subsequent_indent = ' ' * len(name)
            if value.startswith("'") or value.startswith('"'):
                subsequent_indent = '{0} '.format(subsequent_indent)
                
            string.append(
                textwrap.fill(name+value, 79,
                              subsequent_indent=subsequent_indent))
        
        return '\n'.join(string)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_type=False):
        '''Whether two collections of properties are the same.

For vector-valued properties to be equal they must have same size and
be element-wise equal.

Two numerical elements ``a`` and ``b`` are considered equal if
``|a-b|<=atol+rtol|b|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers.

.. versionadded:: 1.7

:Parameters:

    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    ignore_fill_value: `bool`, optional
        If True then the "_FillValue" and "missing_value" properties
        are omitted from the comparison.

    traceback: `bool`, optional
        If True and the collections of properties are different then
        print a traceback stating how they are different.

    ignore_properties: sequence of `str`, optional
        The names of properties to omit from the comparison.

    ignore_data_type: `bool`, optional
        TODO

    ignore_type: `bool`, optional
        TODO

:Returns: 
  
    out: `bool`
        Whether the two collections of propoerties are equal.

**Examples:**

>>> p.equals(p)
True
>>> p.equals(p.copy())
True
>>> p.equals('not a colection of properties')
False

>>> q = p.copy()
>>> q.set_property('foo', 'bar')
>>> p.equals(q)
False
>>> p.equals(q, traceback=True)
Field: Non-common property name: foo
Field: Different properties
False

        '''
        pp = super()._equals_preprocess(other, traceback=traceback,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp
        
        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ('_FillValue', 'missing_value')

        self_properties  = self.properties()
        other_properties = other.properties()

        if ignore_properties:
            for prop in ignore_properties:
                self_properties.pop(prop, None)
                other_properties.pop(prop, None)
        #--- End: if
                
        if set(self_properties) != set(other_properties):
            if traceback:
                _ =  set(self_properties).symmetric_difference(other_properties)
                for prop in set(self_properties).symmetric_difference(other_properties):                    
                    print("{0}: Non-common property name: {1}".format( 
                        self.__class__.__name__, prop))
            return False

        for prop, x in self_properties.items():
            y = other_properties[prop]

            if not self._equals(x, y,
                                rtol=rtol, atol=atol,
                                ignore_fill_value=ignore_fill_value,
                                ignore_data_type=True, #ignore_data_type,
                                traceback=traceback):
                if traceback:
                    print("{0}: Different {1}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        return True
    #--- End: def

#--- End: class
