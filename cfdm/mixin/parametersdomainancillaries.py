from __future__ import print_function
from builtins import super

from . import Parameters


class ParametersDomainAncillaries(Parameters):
    '''Mixin class for parameter- and ancillary-valued terms.

.. versionadded:: 1.7.0

    '''

    def __bool__(self):
        '''Called by the `bool` built-in function.

x.__bool__() <==> bool(x)

.. versionadded:: 1.7.0
 
        '''
        return (super().__bool__() or bool(self.domain_ancillaries()))
    #--- End: def
        
    def __nonzero__(self):
        '''Called by the `bool` built-in function.

x.__nonzero__() <==> bool(x)

.. versionadded:: 1.7.0 

        '''
        return self.__bool__()
    #--- End: def
        
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

        '''
        out = [super().__str__()]

        out.append('Ancillaries: {0}'.format(', '.join(sorted(self.domain_ancillaries()))))
            
        return '; '.join(out)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_type=False):
        '''Whether two instances are the same.

Equality is strict by default. This means that:

* TODO 

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
        if not super().equals(other, rtol=rtol, atol=atol,
                              traceback=traceback,
                              ignore_type=ignore_type):
            return False
        
        # Check that the coordinate conversion ancillary terms
        # match
#        internal_ancillaries = self._internal_ancillaries
        
        domain_ancillaries0 = self.domain_ancillaries()
        domain_ancillaries1 = other.domain_ancillaries()
        if set(domain_ancillaries0) != set(domain_ancillaries1):
            if traceback:
                print(
"{0}: Different domain ancillary terms ({1} != {2})".format(
    self.__class__.__name__,
    set(domain_ancillaries0), set(domain_ancillaries1)))
            return False

        for term, value0 in domain_ancillaries0.items():
            value1 = domain_ancillaries1[term]  
            if value0 is None and value1 is None:
                continue

            if value0 is None or value1 is None:
                if traceback:
                    print(
"{}: Unequal {!r} domain ancillary terms ({!r} != {!r})".format( 
    self.__class__.__name__, term, 
    value0, value1))
                return False

#            if internal_ancillaries:
#                if not self._equals(value0, value1,
#                                    rtol=rtol, atol=atol,
#                                    traceback=traceback,
#                                    ignore_data_type=ignore_data_type,
#                                    ignore_fill_value=ignore_fill_value,
#                                    ignore_type=ignore_type):
#                    if traceback:
#                        print(
#"{}: Unequal {!r} terms ({!r} != {!r})".format( 
#    self.__class__.__name__, term, value0, value1))
#                    return False
        #--- End: for
     
        # Still here? Then the two XXX are as equal as can be
        # ascertained in the absence of domains.
        return True
    #--- End: def

#--- End: class
