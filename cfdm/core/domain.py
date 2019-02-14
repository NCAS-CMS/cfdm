from builtins import super

from . import abstract
from . import mixin

from . import Constructs


class Domain(mixin.ConstructAccess, abstract.Container):
    '''A domain of the CF data model.

The domain represents a set of discrete "locations" in what generally
would be a multi-dimensional space, either in the real world or in a
model's simulated world. These locations correspond to individual data
array elements of a field construct

The domain is defined collectively by the following constructs of the
CF data model: domain axis, dimension coordinate, auxiliary
coordinate, cell measure, coordinate reference and domain ancillary
constructs.

.. versionadded:: 1.7.0

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
        Initialize the metadata constructs from those of *source*.
        
        A new domain may also be instantiated with the
        `fromconstructs` class method.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__()
        
        if source is not None:
            try:                
                constructs = source.constructs
            except AttributeError:
                constructs = self._Constructs(**self._construct_key_base)
                copy = False
                _use_data = True            
            else:
                constructs = constructs._view(ignore=('cell_method',
                                                      'field_ancillary'))
        else:
            constructs = self._Constructs(**self._construct_key_base)
            copy = False
            _use_data = True

        if copy or not _use_data:
            constructs = constructs.copy(data=_use_data)
            
        self._set_component('constructs', constructs, copy=False)
    #--- End: def
    
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------   
    @property
    def constructs(self):
        '''<TODO>
        '''
        return self._get_component('constructs')
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

.. versionadded:: 1.7.0

.. seealso:: `fromconstructs`

:Parameters:

    data: `bool`, optional
        If False then do not copy data. By default data are copied.

:Returns:	

        The deep copy.

**Examples:**

>>> e = d.copy()

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def

    @classmethod
    def fromconstructs(cls, constructs, copy=False):
        '''Create a domain from existing metadata constructs.

.. versionadded:: 1.7.0

:Parameters:

    constructs: `Constructs`
        TODO

    copy: bool, optional
        If True then deep copy the metadata constructs prior to
        initialization. By default the metadata constructs are not
        copied.

:Returns:

    `Domain`
        TODO

**Examples:**

>>> d = Domain.fromconstructs(f.constructs)

        '''
        domain = cls()
        domain._set_component('constructs',
                              constructs._view(ignore=('cell_method',
                                                       'field_ancillary')),
                              copy=copy)
        return domain
    #--- End: def
            
#--- End: class
