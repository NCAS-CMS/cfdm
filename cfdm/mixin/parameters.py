from __future__ import print_function
from builtins import super

from . import Container


class Parameters(Container):
    '''Mixin class for parameters.

.. versionadded:: 1.7.0

    '''

    def __bool__(self):
        '''Called by the `bool` built-in function.

x.__bool__() <==> bool(x)

.. versionadded:: 1.7.0

        '''
        return bool(self.parameters())
    #--- End: def
        
    def __nonzero__(self):
        '''Called by the `bool` built-in function.

x.__nonzero__() <==> bool(x)

.. versionadded:: 1.7.0

        '''
        return bool(self.parameters())
    #--- End: def
        
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7.0

        '''
        return 'Parameters: {0}'.format(', '.join(sorted(self.parameters())))
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_type=False):
        '''Whether two instances are the same.

Equality is strict by default. This means that:

* TODO (see the *ignore_data_type* parameter)

Two numerical elements ``a`` and ``b`` are considered equal if
``|a-b|<=atol+rtol|b|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

Any type of object may be tested but, in general, equality is only
possible with another object of the same type, or a subclass of
one. See the *ignore_type* parameter.

:Parameters:

    other:
        The object to compare for equality.

    atol: `float`, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.

    rtol: `float`, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    traceback: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. If *ignore_type* is True then equality is
        possible for any object with a compatible API.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns: 

    out: `bool`
       Whether the two instances are equal.

**Examples:**

TODO

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
