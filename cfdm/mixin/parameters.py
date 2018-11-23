from __future__ import print_function
from builtins import super

from . import Container


class Parameters(Container):
    '''Mixin class for parameters.

    '''

    def __bool__(self):
        '''TODO 

.. versionadded:: 1.7

        '''
        return bool(self.parameters())
    #--- End: def
        
    def __nonzero__(self):
        '''TODO 

.. versionadded:: 1.7
        '''
        return bool(self.parameters())
    #--- End: def
        
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''
        return 'Parameters: {0}'.format(', '.join(sorted(self.parameters())))
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_type=False):
        '''TODO True if two instances are equal, False otherwise.

:Parameters:

    other:
        The object to compare for equality.

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns: 

    out: `bool`
        Whether or not the two instances are equal.

:Examples:

        '''
        pp = super()._equals_preprocess(other, traceback=traceback,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp
        
#        # Check for object identity
#        if self is other:
#            return True
#        
#        # Check that each object is of the same type
#        if ignore_type:
#            if not isinstance(other, self.__class__):
#                other = type(self)(source=other, copy=False)
#        elif not isinstance(other, self.__class__):
#            if traceback:
#                print("{0}: Incompatible types: {0}, {1}".format(
#		    self.__class__.__name__,
#		    other.__class__.__name__))
#            return False

#        if not super().equals(
#                other, #rtol=rtol, atol=atol,
#                traceback=traceback,
#                ignore_type=ignore_type):
#            return False
        
        # Check that the coordinate conversion parameter terms match
        parameters0 = self.parameters()
        parameters1 = other.parameters()
        if set(parameters0) != set(parameters1):
            if traceback:
                print(
"{0}: Different parameter-valued terms ({1} != {2})".format(
    self.__class__.__name__,
    set(parameters0), set(parameters1)))
            return False

        # Check that the parameter values are equal
        for term, value0 in parameters0.items():            
            value1 = parameters1[term]  

            if value0 is None and value1 is None:
                # Parameter values are both None
                continue

            if not self._equals(value0, value1, rtol=rtol, atol=atol,
                                traceback=traceback,
                                ignore_data_type=True, #ignore_data_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_type=ignore_type):
                if traceback:
                    print(
"{}: Unequal {!r} terms ({!r} != {!r})".format( 
    self.__class__.__name__, term, value0, value1))
                return False
        #--- End: for

        # Still here? Then the two parameter collections are equal
        return True
    #--- End: def

#--- End: class
