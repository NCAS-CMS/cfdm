from builtins import super

from . import mixin
from . import core


class CoordinateConversion(mixin.Parameters, #mixin.ParametersDomainAncillaries,
                           core.CoordinateConversion):
    '''A coordinate conversion component of a coordinate reference
construct of the CF data model.

A coordinate conversion formula converting coordinate values taken
from the dimension or auxiliary coordinate constructs to a different
coordinate system. A term of the conversion formula can be a scalar or
vector parameter which does not depend on any domain axis constructs,
may have units, or may be a descriptive string (such as the projection
name "mercator"), or it can be a reference to a domain ancillary
construct (such as one containing spatially varying orography data). A
coordinate reference construct relates the coordinate values of the
field to locations in a planetary reference frame.

.. versionadded:: 1.7

    '''
   
    # Ancillary-valued terms are stored as references to external
    # objects
    _internal_ancillaries = False

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''
        out = [super().__str__()]

        out.append('Ancillaries: {0}'.format(', '.join(sorted(self.domain_ancillaries()))))
            
        return '; '.join(out)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_construct_type=False):
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
        if not super().equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_construct_type=ignore_construct_type):
            return False
        
        # Check that the coordinate conversion ancillary terms
        # match
        internal_ancillaries = self._internal_ancillaries
        
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

            if internal_ancillaries:
                if not self._equals(value0, value1,
                                    rtol=rtol, atol=atol,
                                    traceback=traceback,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    ignore_construct_type=ignore_construct_type):
                    if traceback:
                        print(
"{}: Unequal {!r} terms ({!r} != {!r})".format( 
    self.__class__.__name__, term, value0, value1))
                    return False
        #--- End: for
     
        # Still here? Then the two XXX are as equal as can be
        # ascertained in the absence of domains.
        return True
    #--- End: def
    
#--- End: class
