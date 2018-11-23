from __future__ import print_function
from builtins import object


class Equals(object):
    '''Mixin class for TODO

    '''
    def equals_preprocess(self, other, traceback=False,
                          ignore_construct_type=False):
        '''TODO

        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each object is of the same type
        if ignore_construct_type:
            if not isinstance(other, self.__class__):
                other = type(self)(source=other, copy=False)
        elif not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible types: {0}, {1}".format(
		    self.__class__.__name__,
		    other.__class__.__name__))
            return False

        return other
    #--- End: def
    
#--- End: class
