from __future__ import print_function
from builtins import object

import textwrap

import numpy
import sys


class Container(object):
    '''Mixin class for storing object components.

.. versionadded:: 1.7

    '''
    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

.. versionadded:: 1.7

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   str(self))
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''
        out = sorted(self._components)
        return ', '.join(out)
    #--- End: def

    @classmethod
    def _equals(self, x, y, rtol=None, atol=None, **kwargs):
        '''TODO

.. versionadded:: 1.7

        '''
        if rtol is None:
            rtol = sys.float_info.epsilon
        if atol is None:
            atol = sys.float_info.epsilon

        eq = getattr(x, 'equals', None)
        if callable(eq):
            # x has a callable equals method
            return eq(y, rtol=rtol, atol=atol, **kwargs)
        
        eq = getattr(y, 'equals', None)
        if callable(eq):
            # y has a callable equals method
            return eq(x, rtol=rtol, atol=atol, **kwargs)
        
        if isinstance(x, numpy.ndarray) or isinstance(y, numpy.ndarray):
            if numpy.shape(x) != numpy.shape(y):
                return False
            
            # THIS IS WHERE SOME NUMPY FUTURE WARNINGS ARE COMING FROM
   
            x_is_masked = numpy.ma.isMA(x)
            y_is_masked = numpy.ma.isMA(y)

            if not (x_is_masked or y_is_masked):
                try:            
                    return numpy.allclose(x, y, rtol=rtol, atol=atol)
                except (IndexError, NotImplementedError, TypeError):
                    return numpy.all(x == y)
            else:
                if x_is_masked and y_is_masked:
                    if (x.mask != y.mask).any():
                        return False
                elif ((x_is_masked and x.mask.any()) or
                      (y_is_masked and y.mask.any())):
                    return False

                try:
                    return numpy.ma.allclose(x, y, rtol=rtol, atol=atol)
                except (IndexError, NotImplementedError, TypeError):
                    out = numpy.ma.all(x == y)
                    if out is numpy.ma.masked:
                        return True
                    else:
                        return out
        else:
            return x == y
    #--- End: def
    
    def equals(self, other, #rtol=None, atol=None,
               traceback=False,
               ignore_construct_type=False):
        '''TODO

..versionadded:: 1.7

:Parameters:

    TODO

:Returns:

    TODO

**Examples:**

TODO
        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each instance is of the same type
        if not ignore_construct_type and not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible types: {0}, {1}".format(
			self.__class__.__name__,
			other.__class__.__name__))
            return False

        return True
    #--- End: def
        
#--- End: class
