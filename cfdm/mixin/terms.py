import abc

from .container import Container


class Terms(Container):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    def __nonzero__(self):
        '''
        '''
        return bool(self.parameters()) or bool(self.domain_ancillaries())
        
        
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = []

        parameters = self.parameters()
        if parameters:
            out.append('Parameters: {0}'.format(', '.join(sorted(parameters))))
            
        domain_ancillaries = self.domain_ancillaries()
        if domain_ancillaries:
            out.append('Domain ancillaries: {0}'.format(', '.join(sorted(domain_ancillaries))))
            
        return '; '.join(out)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_construct_type=False):
        '''True if two instances are equal, False otherwise.

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
        if not super(Terms, self).equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_construct_type=ignore_construct_type):
	    return False
        
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

        # Check that the coordinate conversion domain ancillary terms
        # match
        ancillaries0 = self.domain_ancillaries()
        ancillaries1 = other.domain_ancillaries()
        if set(ancillaries0) != set(ancillaries1):
            if traceback:
                print(
"{0}: Different domain ancillary-valued terms ({1} != {2})".format(
    self.__class__.__name__,
    set(ancillaries0), set(ancillaries1)))
            return False

        for term, value0 in ancillaries0.iteritems():            
            value1 = ancillaries1[term]  
            if value0 is None or (value1 is None and value0 is not None):
                if traceback:
                    print(
"{}: Unequal {!r} domain ancillary terms ({!r} != {!r})".format( 
    self.__class__.__name__, term, 
    value0, value1))
                return False
        #--- End: for
     
        # Check that the coordinate conversion parameter term
        # values are equal.
        for term, value0 in parameters0.iteritems():            
            value1 = parameters1[term]  

            if value0 is None and value1 is None:
                # Term values are None in both coordinate
                # references
                continue
                
            if not self._equals(value0, value1, rtol=rtol, atol=atol,
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

        # Still here? Then the two coordinate references are as equal
        # as can be ascertained in the absence of domains.
        return True
    #--- End: def

#--- End: class
