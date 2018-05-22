import abc

import abstract
import mixin

from .constructs import Constructs


class Domain(mixin.ConstructAccess, abstract.Properties):
    '''A domain of the CF data model.

A domain represents a set of discrete "locations" in what generally
would be a multi-dimensional space, either in the real world or in a
model's simulated world.

The domain is defined collectively by other constructs included in a
field construct which describe measurement locations and cell
properties:

====================  ================================================
Construct             Description
====================  ================================================
Domain axis           Independent axes of the domain stored in
                      `DomainAxis` objects

Dimension coordinate  Cell locations stored in `DimensionCoordinate`
                      objects

Auxiliary coordinate  Cell locations stored in `AuxiliaryCoordinate`
                      objects

Coordinate reference  Coordinate systems stored in
                      `CoordinateReference` objects

Domain ancillary      Ancillary values for cell locations in
                      alternative coordinate systems stored in
                      `DomainAncillary` objects

Cell measure          Cell sizes stored in `CellMeasure` objects
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
            try:                
                constructs = source._get_constructs()
            except AttributeError:
                constructs = self._Constructs(**self._construct_key_base)
            else:
                constructs = constructs.subset(self._construct_key_base.keys(), copy=False)
                if copy or not _use_data:
                    constructs = constructs.copy(data=_use_data)
        #--- End: if

        self._set_component('constructs', None, constructs)
    #--- End: def
    
    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.size for domain_axis in self.domain_axes().values()])

        return '<{0}: {1}>'.format(self.__class__.__name__, shape)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

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
                for term, value in coordinate_conversion.ancillaries().iteritems():
                    if key == value:
                        coordinate_conversion.set_ancillary(term, None)
                    
                for coord_key in ref.coordinates():
                    if key == coord_key:
                        ref.del_coordinate(coord_key)
                        break
        #--- End: if
        
        return self._get_constructs().del_construct(key)
    #--- End: def


#--- End: class
