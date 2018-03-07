from copy import deepcopy

from ..structure

from .functions import RTOL, ATOL, equals

# ====================================================================
#

#
# ====================================================================

class Collection(structure.Collection):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        obj._equals = equals
        return obj
    #--- End: def

    @classmethod
    def _equals(self, x, y, rtol=None, atol=None, **kwargs):
        '''
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
                else:
                    return False

                try:
                    return numpy.ma.allclose(x, y, rtol=rtol, atol=atol)
                except (IndexError, NotImplementedError, TypeError):
                    out = numpy.ma.all(x == y)
                    if out is numpy.ma.masked:
                        return True
                    else:
                        return out
                
#            return _numpy_allclose(x, y, rtol=rtol, atol=atol)

        else:
            return x == y
    #--- End: def
    
    def equals(self, other, **kwargs):
        '''
        '''
        if set(self) != set(other):
            if traceback:
                print("{0}: Different parameters: {1}, {2}".format( 
                    self.__class__.__name__, self, other)
            return False
       
        for key, value in self.iteritems():
            if not self._equals(value, other[key], **kwargs)
                if traceback:
                    print("{0}: Different parameter {1!r}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        return True
    #--- End: def
    
#--- End: class
