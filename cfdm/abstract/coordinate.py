from collections import abc

from .boundedarrayconstruct import AbstractBoundedVariable


# ====================================================================
#
# Generic coordinate object
#
# ====================================================================

class Coordinate(AbstractBoundedVariable):
    '''Base class for a CFDM dimension or auxiliary coordinate construct.


**Attributes**

=================  =========  ========================================
Attribute          Type       Description
=================  =========  ========================================
`climatology`      ``bool``   Whether or not the bounds are intervals
                              of climatological time. Presumed to be
                              False if unset.

`geometry`         ``bool``   Whether or not the bounds are
                              geometries. Presumed to be False if 
                              unset.

`part_node_count`  ``Array``  

`interior_ring`    ``Array``  
=================  =========  ========================================

    '''
    __metaclass__ = abc.ABCMeta

    pass                 
#--- End: class
