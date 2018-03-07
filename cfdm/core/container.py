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
