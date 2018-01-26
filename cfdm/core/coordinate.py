from collections import abc

from .boundedvariable import BoundedVariableMixin

from ..structure import Coordinate as StructuralCoordinate


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class Coordinate(StructuralCoordinate, BoundedVariableMixin):
    '''

Base class for a CF dimension or auxiliary coordinate construct.


**Attributes**

===============  ========  ===================================================
Attribute        Type      Description
===============  ========  ===================================================
`!climatology`   ``bool``  Whether or not the bounds are intervals of
                           climatological time. Presumed to be False if unset.
===============  ========  ===================================================

'''
    __metaclass__ = abc.ABCMeta
#--- End: class
