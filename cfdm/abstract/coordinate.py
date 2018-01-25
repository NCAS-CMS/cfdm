from collections import abc

from .boundedarrayconstruct import AbstractBoundedArrayConstruct


# ====================================================================
#
# Generic coordinate object
#
# ====================================================================

class AbstractCoordinate(AbstractBoundedArray):
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
    
    def __init__(self, properties={}, data=None, bounds=None,
                 source=None, climatology=None, geometry=None,
                 copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.
  
    data: `Data`, optional
        Provide the new instance with an N-dimensional data array.
  
    bounds: `Data` or `Bounds`, optional
        Provide the new instance with cell bounds.
  
    source: `Variable`, optional
        Take the attributes, CF properties and data array from the
        source object. Any attributes, CF properties or data array
        specified with other parameters are set after initialisation
        from the source instance.
  
    copy: `bool`, optional
        If False then do not copy arguments prior to
        initialization. By default arguments are deep copied.
  
        '''
        # Set attributes, properties, data and ancillaries
        super(AbstractCoordinate, self).__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy)

        # ------------------------------------------------------------
        # Ancillary attributes (note that these may already have been
        # set from source)
        # ------------------------------------------------------------
        properties = self.properties()

        if climatology is None:
            if 'climatology' in properties:
                climatology = self.getprop('climatology')
                self.delprop('climatology')
        #--- End: if
        if climatology is not None:
            self.climatology = climatology

        if geometry is None:
            if 'geometry' in properties:
                geometry = self.getprop('geometry')
                self.delprop('geometry')
        #--- End: if
        if geometry is not None:
            self.geometry = geometry
    #--- End: def
                 
#--- End: class
