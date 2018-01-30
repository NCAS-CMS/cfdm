from collections import abc

import ..structure

# ====================================================================
#
# Domain axis object
#
# ====================================================================

class DomainAxis(structure.DomainAxis):
    '''A CF domain axis construct.

A domain axis construct specifies the number of points along an
independent axis of the domain. It comprises a positive integer
representing the size of the axis. In CF-netCDF it is usually defined
either by a netCDF dimension or by a scalar coordinate variable, which
implies a domain axis of size one. The field construct's data array
spans the domain axis constructs of the domain, with the optional
exception of size one axes, because their presence makes no difference
to the order of the elements.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, size=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    size: `int`, optional
        The size of the domain axis.

    source: `DomainAxis`

        '''
        super(DomainAxis).__init__(size=size, source=source, copy=copy)
        
        if source:
            ncdim = source.get_ncdim(None)
            if ncdim is not None:
                self.set_ncdim(ncdim)
    #--- End: def
    
    def equals(self, other, traceback=False, *kwargs):
        '''Return True if two domain axis objects are equal.

:Parameters:

    other : object
        The object to compare for equality.

    traceback : bool, optional
        If True then print a traceback highlighting where the two
        domain axes differ.

    atol : *optional*
        Ignored.

    rtol : *optional*
        Ignored.

    ignore : *optional*
        Ignored.

    ignore_fill_value : *optional*
        Ignored.

:Returns: 
  
    out : bool
        Whether or not the two domain axes are equal.
        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each instance is of the same type
        if not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible types: {0}, {1}".format(
			self.__class__.__name__,
			other.__class__.__name__))
	    return False

        # Check that each axis has the same size
        self_size  = self.get_size(None)
        other_size = other.get_size(None)
        if not self_size == other_size:
            if traceback:
                print("{0}: Different axis sizes: {1} != {2}".format(
			self.__class__.__name__, self_size, other_size))
	    return False

        return True
    #--- End: def

    def get_ncdim(self, *default):
        '''
        '''
        return self._get_attribute('ncdim', *default)
    #--- End: def

    def set_ncdim(self, ncdim):
        '''
        '''
        self._set_attribute('ncdim', ncdim)
    #--- End: def

    def del_ncdim(self):
        '''
        '''
        return self._del_attribute('ncdim')
    #--- End: def

#--- End: class
