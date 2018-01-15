from collections import abc

from .boundedarrayconstruct import AbstractBoundedArrayConstruct


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class AbstractCoordinate(AbstractBoundedArrayConstruct):
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
