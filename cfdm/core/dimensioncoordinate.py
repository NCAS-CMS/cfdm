from .coordinate import Coordinate

# ====================================================================
#
# DimensionCoordinate object
#
# ====================================================================

class DimensionCoordinate(Coordinate):
    '''A CF dimension coordinate construct.

**Attributes**

==============  ========  ============================================
Attribute       Type      Description
==============  ========  ============================================
`!climatology`  ``bool``  Whether or not the bounds are intervals of
                          climatological time. Presumed to be False if
                          unset.
==============  ========  ============================================

    '''
    @property
    def isdimension(self):
        '''True, denoting that the variable is a dimension coordinate object.

.. seealso::`role`

.. seealso:: `isboundedvariable`, `iscoordinate`, `isvariable`

:Examples:

>>> c.isdimension
True

        '''
        return True
    #--- End: def
  
    def isvalid(self, traceback=False):
        '''
        '''
        if self.hasdata:
            if self.ndim > 1:
                if traceback:
                    print(
"Dimension coordinate object must be 1-d (not {}-d)".format(self.ndim))
            return False

        elif self.hasbounds:
            if self.bounds.ndim != bounds.ndim + 1:
                if traceback:
                    print (
"Expected {}-d bounds (got {}-d)".format(self.ndim+1, self.ndim))
            return False

        # Check data type
        if self.dtype.kind not in ('i', 'u', 'f'):
            if traceback:
                print ("Not numeric")
            return False

        # Check for strict monotonicity
        array = self.data.array
        steps = array[1:] - array[:-1]
        if not ((steps > 0).all() or (steps < 0).all()):
            if traceback:
                print ("Not strictly monotonic")
            return False

        return True                
#--- End: class
