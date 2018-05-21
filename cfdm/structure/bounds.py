import abc

import abstract

#class Bounds(mixin.Ancillaries, abstract.PropertiesData):
class Bounds(abstract.PropertiesData):
    '''Coordinate bounds
    '''
    __metaclass__ = abc.ABCMeta

#    def __init__(self, properties={}, data=None, cell_type=None,
#                 ancillaries=None, source=None, copy=True,
#                 _use_data=True):
#        '''**Initialization**
#
#:Parameters:
#
#    properties: `dict`, optional
#        Set descriptive properties. The dictionary keys are property
#        names, with corresponding values. Ignored if the *source*
#        parameter is set.
#
#          *Example:*
#             ``properties={'standard_name': 'longitude'}``
#        
#        Properties may also be set after initialisation with the
#        `properties` and `set_property` methods.
#  
#    data: `Data`, optional
#        Set the data array. Ignored if the *source* parameter is set.
#        
#        The data array also may be set after initialisation with the
#        `set_data` method.
#  
#    bounds: `Bounds`, optional
#        Set the bounds array. Ignored if the *source* parameter is
#        set.
#        
#        The bounds array also may be set after initialisation with the
#        `set_bounds` method.
#  
#    source: optional
#        Initialise the *properties*, *data* and *bounds* parameters
#        from the object given by *source*.
#  
#    copy: `bool`, optional
#        If False then do not deep copy arguments prior to
#        initialization. By default arguments are deep copied.
#
#        '''
#        # Initialise properties and data
#        super(PropertiesData, self).__init__(
#            properties=properties,
#            data=data,
#            source=source,
#            copy=copy,
#            _use_data=_use_data)
#
#        if source is not None:
#            try:
#                cell_type = source.get_cell_type(None)
#            except AttributeError:
#                cell_type = None
#                
#            try:
#                ancillaries = source.get_ancillaries()
#            except AttributeError:
#                ancillaries = None
#        #--- End: if
#
#        if cell_type is not None:
#            self.set_cell_type(cell_type)
#
#        if ancillaries is None:
#            ancillaries = {}
#        elif copy or not _use_data:
#            ancillaries = ancillaries.copy()
#            for key, value in ancillaries.items():
#                try:
#                    ancillaries[key] = value.copy(data=_use_data)
#                except AttributeError:
#                    ancillaries[key] = deepcopy(value)
#        #--- End: if
#    #--- End: def
    
#--- End: class
