from .coordinate import Coordinate

# ====================================================================
#
# AuxiliaryCoordinate object
#
# ====================================================================

class AuxiliaryCoordinate(Coordinate):
    '''

A CF auxiliary coordinate construct.


**Attributes**

===============  ========  ===================================================
Attribute        Type      Description
===============  ========  ===================================================
`!climatology`   ``bool``  Whether or not the bounds are intervals of
                           climatological time. Presumed to be False if unset.
===============  ========  ===================================================

'''
    @property
    def isauxiliary(self):
        '''True, denoting that the variable is an auxilliary coordinate
object.

.. seealso:: `iscoordinate`, `isboundedvariable`, `isvariable`

:Examples:

>>> c.isauxiliary
True

        '''
        return True
    #--- End: def

#--- End: class
