from __future__ import print_function
from builtins import object

import sys
import textwrap

import numpy

from ..functions import ATOL, RTOL

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

:Parameters:

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

        '''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        eq = getattr(x, 'equals', None)
        if callable(eq):
            # --------------------------------------------------------
            # x has a callable "equals" method
            # --------------------------------------------------------
            return eq(y, rtol=rtol, atol=atol, **kwargs)
        
        eq = getattr(y, 'equals', None)
        if callable(eq):
            # --------------------------------------------------------
            # y has a callable "equals" method
            # --------------------------------------------------------
            return eq(x, rtol=rtol, atol=atol, **kwargs)
        
        if numpy.shape(x) != numpy.shape(y):
            return False
        
        if isinstance(x, numpy.ndarray) or isinstance(y, numpy.ndarray):
            # --------------------------------------------------------
            # x or y is a numpy array
            # --------------------------------------------------------
            
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
            # --------------------------------------------------------
            # x and y are not numpy arrays
            # --------------------------------------------------------
#            return x == y
            try:
                return numpy.allclose(x, y, rtol=rtol, atol=atol)
            except (IndexError, NotImplementedError, TypeError):
                return x == y
    #--- End: def
    
#    def equals(self, other, traceback=False,
#               ignore_construct_type=False):
#        '''TODO
#
#..versionadded:: 1.7
#
#:Parameters:
#
#    TODO
#
#:Returns:
#
#    TODO
#
#**Examples:**
#
#TODO
#        '''
#        # Check for object identity
#        if self is other:
#            return True
#
#        # Check that each instance is of the same type
#        if ignore_construct_type and not isinstance(other, self.__class__):
#            other = type(self)(source=other, copy=False)
#        else:
#        # Check that each instance is of the same type
#            if not ignore_construct_type and not isinstance(other, self.__class__):
#                if traceback:
#                    print("{0}: Incompatible types: {0}, {1}".format(
#			self.__class__.__name__,
#			other.__class__.__name__))
#                return False
#        #--- End: if
#
#        return True
#    #--- End: def

    def _equals_preprocess(self, other, traceback=False,
                          ignore_construct_type=False):
        '''TODO

        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each object is of compatible type
        if ignore_construct_type:
            if not isinstance(other, self.__class__):
                other = type(self)(source=other, copy=False)
        elif not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible type: {1}".format(
		    other.__class__.__name__))
            return False

        return other
    #--- End: def
    
#--- End: class
