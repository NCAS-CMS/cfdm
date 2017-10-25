# ====================================================================
#
# DomainAxis object
#
# ====================================================================

class DomainAxis(object):
    '''A CF domain axis construct.

A domain axis construct specifies the number of points along an
independent axis of the domain. It comprises a positive integer
representing the size of the axis. In CF-netCDF it is usually defined
either by a netCDF dimension or by a scalar coordinate variable, which
implies a domain axis of size one. The field construct's data array
spans the domain axis constructs of the domain, with the optional
exception of size one axes, because their presence makes no difference
to the order of the elements.

**Attributes**

=========  =======  ==================================================
Attribute  Type     Description
=========  =======  ==================================================
`!size`    `int`    The size of the domain axis.

`!ncdim`   `str`    The name of this domain axis as a netCDF
                    dimension.
=========  =======  ==================================================

    '''
    def __init__(self, size=None, ncdim=None):
        '''**Initialization**

:Parameters:

    size: `int`, optional
        The size of the domain axis.

    ncdim: `str`, optional
        The name of this domain axis as a netCDF dimension.

        '''
        self.size  = size
        self.ncdim = ncdim
    #--- End: def

    def __deepcopy__(self, memo):
        '''

Called by the `copy.deepcopy` standard library function.

'''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''

Called by the `str` built-in function.

x.__str__() <==> str(x)
'''
        return str(self.size)
    #--- End: def

    def __eq__(self, other):
        return self.size == other

    def __ne__(self, other):
        return not self == other

    def copy(self):
        '''

Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

'''
        X = type(self)
        new = X.__new__(X)

        # This is OK, for now, because values of self.__dict__ are
        # immutable
        new.__dict__ = self.__dict__.copy()

        return new
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, ignore=(), _set=False):
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
        #--- End: if

        # Check that each axis has the same size
        if not self.size == other.size:
            if traceback:
                print("{0}: Different axis sizes: {1} != {2}".format(
			self.__class__.__name__, self.size, other.size))
	    return False
        #--- End: if

        return True
    #--- End: def

#--- End: class


## ====================================================================
##
## Axes object
##
## ====================================================================
#class Axes(dict):
#    '''
#    A dictionary of domain axis objects with extra methods.
#
#:Example:
#
#>>> a
#{'dim1': <CF DomainAxis: 73>,
# 'dim0': <CF DomainAxis: 12>,
# 'dim2': <CF DomainAxis: 96>}
#>>> a.equals(a)
#True
#
#    '''
#    def __deepcopy__(self, memo):
#        '''
#Called by the `copy.deepcopy` standard library function.
#'''
#        return self.copy()
#    #--- End: def
#
#    def copy(self):
#        '''Return a deep copy.
#        
#``a.copy()`` is equivalent to ``copy.deepcopy(a)``.
#        
#:Returns:
#
#    out: `Axes`
#        The deep copy.
#
#:Examples:
#
#>>> b = a.copy()
#
#'''
#        new = type(self)()
#        for key, value in self.iteritems():
#            new[key] = value.copy()
#    
#        return new
#    #--- End: def
#
#    def equals(self, other, rtol=None, atol=None,
#               ignore_data_type=False, ignore_fill_value=False,
#               traceback=False):
#        '''
#
#:Parameters:
#
#    other:
#        The object to compare for equality.
#
#    traceback: `bool`, optional
#        If True then print a traceback highlighting where the two
#        instances differ.
#
#    atol: optional
#        Ignored.
#
#    rtol: optional
#        Ignored.
#
#    ignore_fill_value: optional
#        Ignored.
#
#:Returns: 
#
#    out: `bool`
#        Whether or not the two instances are equal.
#
#:Examples:
#
#>>> d.equals(e)
#True
#>>> d.equals(f)
#False
#>>> d.equals(f, traceback=True)
#
#'''
#        if self is other:
#            return True
#
#        # Check that each instance is the same type
#
#        if type(self) != type(other):
#            if traceback:
#                print("{0}: Different types: {0}, {1}".format(
#                    self.__class__.__name__, other.__class__.__name__))
#            return False
#        #--- End: if
#
#        self_sizes  = [d.size for d in self.values()]
#        other_sizes = [d.size for d in other.values()]
#        
#        if sorted(self_sizes) != sorted(other_sizes):
#            # There is not a 1-1 correspondence between axis sizes
#            if traceback:
#                print("{}: Different domain axis sizes: {} != {}".format(
#                    self.__class__.__name__,
#                    sorted(self.values()),
#                    sorted(other.values())))
#            return False
#        #--- End: if
#
#        # ------------------------------------------------------------
#        # Still here? Then the two collections of domain axis objects
#        # are equal
#        # ------------------------------------------------------------
#        return True
#    #--- End: def
#
##--- End: class
