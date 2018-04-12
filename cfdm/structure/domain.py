import abc

import abstract
import mixin

from .constructs import Constructs


# ====================================================================
#
# Domain object
#
# ====================================================================

class Domain(mixin.ConstructAccess, abstract.Properties):
    '''A CF Domain construct.

The domain is defined collectively by teh following constructs, all of
which are optional:

====================  ================================================
Construct             Description
====================  ================================================
Domain axis           Independent axes of the domain stored in
                      `DomainAxis` objects

Dimension coordinate  Domain cell locations stored in
                      `DimensionCoordinate` objects

Auxiliary coordinate  Domain cell locations stored in
                      `AuxiliaryCoordinate` objects

Coordinate reference  Domain coordinate systems stored in
                      `CoordinateReference` objects

Domain ancillary      Cell locations in alternative coordinate systems
                      stored in `DomainAncillary` objects

Cell measure          Domain cell size or shape stored in
                      `CellMeasure` objects
====================  ================================================

    '''
    __metaclass__ = abc.ABCMeta

    # Define the base of the identity keys for each construct type
    _construct_key_base = {'auxiliary_coordinate': 'auxiliarycoordinate',
                           'cell_measure'        : 'cellmeasure',
                           'coordinate_reference': 'coordinatereference',
                           'dimension_coordinate': 'dimensioncoordinate',
                           'domain_ancillary'    : 'domainancillary',
                           'domain_axis'         : 'domainaxis',
    }
    

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
       
        obj._Constructs = Constructs

        return obj
    #--- End: def
    
    def __init__(self, properties=None, source=None, copy=True,
                 _use_data=True, _view_constructs=None):
        '''**Initialization**

:Parameters:

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super(Domain, self).__init__(properties=properties,
                                     source=source, copy=copy)
        
        if _view_constructs is not None:
            constructs = self._Constructs(source=_view_constructs,
                                          view=True,
                                          ignore=('cell_method', 'field_ancillary'))
        elif source is None:
            constructs = self._Constructs(**self._construct_key_base)
        else:
            constructs = source._get_constructs()
            constructs = constructs.subset(self._construct_key_base.keys(), copy=False)
            if copy or not _use_data:
                constructs = constructs.copy(data=_use_data)
        #--- End: if

        self._set_component(3, 'constructs', None, constructs)
    #--- End: def
    
    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.size for domain_axis in self.domain_axes().values()])

        return '<{0}: {1}>'.format(self.__class__.__name__, shape)
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        return 'STRINASDAs da sa'
    #-- End: def
        
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        return self._get_component('constructs', None, *default)
    #--- End: def
    
    def del_construct(self, key):
        '''
        '''
        if key in self.domain_axes():
            for k, v in self.array_constructs().iteritems():
                if key in self.construct_axes(k):
                    raise ValueError("asda ;wo3in dp08hi n")
        else:
            # Remove pointers to removed construct in coordinate
            # reference constructs
            for ref in self.coordinate_references().itervalues():
                coordinate_conversion = ref.coordinate_conversion
                for term, value in coordinate_conversion.domain_ancillaries().iteritems():
                    if key == value:
                        coordinate_conversion.set_domain_ancillary(term, None)
                    
                for coord_key in ref.coordinates():
                    if key == coord_key:
                        ref.del_coordinate(coord_key)
                        break
        #--- End: if
        
        return self._get_constructs().del_construct(key)
    #--- End: def

    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: for
    

#--- End: class
