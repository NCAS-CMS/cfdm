from builtins import super

from . import abstract
from . import mixin

from . import Constructs


class Domain(mixin.ConstructAccess, abstract.Container):
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

    # Define the base of the identity keys for each construct type
    _construct_key_base = {'auxiliary_coordinate': 'auxiliarycoordinate',
                           'cell_measure'        : 'cellmeasure',
                           'coordinate_reference': 'coordinatereference',
                           'dimension_coordinate': 'dimensioncoordinate',
                           'domain_ancillary'    : 'domainancillary',
                           'domain_axis'         : 'domainaxis',
    }
    

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance
    #--- End: def
    
    def __init__(self, source=None, copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    source: optional
        TODO
        Initialise the domain from the constructs of *source*,
        ignoring any cell method or field ancillary constructs.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__()
        
        if source is not None:
            try:                
                constructs = source._get_constructs()
            except AttributeError:
                constructs = self._Constructs(**self._construct_key_base)
                copy = False
                _use_data = True            
            else:
                constructs = constructs.view(ignore=('cell_method',
                                                     'field_ancillary'))
        else:
            constructs = self._Constructs(**self._construct_key_base)
            copy = False
            _use_data = True

        if copy or not _use_data:
            constructs = constructs.copy(data=_use_data)
            
        self._set_component('constructs', constructs, copy=False)
    #--- End: def
    
#    def __repr__(self):
#        '''x.__repr__() <==> repr(x)
#
#        '''
#        shape = sorted([domain_axis.size for domain_axis in list(self.domain_axes().values())]#)
#
#        return '<{0}: {1}>'.format(self.__class__.__name__, shape)
#    #--- End: def
#
#    def __str__(self):
#        '''x.__str__() <==> str(x)
#
#        '''
#        return 'STRINASDAs da sa'
#    #-- End: def

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _get_constructs(self, *default):
        '''TODO

.. versionadded:: 1.7
        
        '''
        return self._get_component('constructs', *default)
    #--- End: def
    
    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

.. versionadded:: 1.7

.. seealso:: `fromconstructs`

:Parameters:

    data: `bool`, optional
        If False then do not copy data. By default data are copied.

:Returns:	

    out:
        The deep copy.

**Examples:**

>>> e = d.copy()

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def

    def del_construct(self, key):
        '''
        '''
        if key in self.domain_axes():
            for k, v in self.array_constructs().items():
                if key in self.construct_axes(k):
                    raise ValueError("asda ;wo3in dp08hi n")
        else:
            # Remove pointers to removed construct in coordinate
            # reference constructs
            for ref in self.coordinate_references().values():
                coordinate_conversion = ref.coordinate_conversion
                for term, value in coordinate_conversion.domain_ancillaries().items():
                    if key == value:
                        coordinate_conversion.set_ancillary(term, None)
                    
                for coord_key in ref.coordinates():
                    if key == coord_key:
                        ref.del_coordinate(coord_key)
                        break
        #--- End: if
        
        return self._get_constructs().del_construct(key)
    #--- End: def

    @classmethod
    def fromconstructs(cls, constructs):
        '''TODO

.. versionadded:: 1.7

.. seealso:: `copy`

:Parameters:

    constructs: `Constructs`
        
:Returns:

    out: `Domain`
        TODO

**Examples:**

>>> d = Domain.fromconstructs(f._get_constructs())
        
        '''
        domain = cls()
        domain._set_component('constructs',
                              constructs.view(ignore=('cell_method',
                                                      'field_ancillary')),
                              copy=False)
        return domain
    #--- End: def
            
#--- End: class
