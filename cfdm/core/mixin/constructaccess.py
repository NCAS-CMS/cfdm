from builtins import object
from future.utils import with_metaclass

import abc


class ConstructAccess(with_metaclass(abc.ABCMeta, object)):
    '''Mixin class for accessing an embedded `Constructs` object.

    '''   
    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''Return the `Constructs` object

:Parameters:

    default: optional
        If set then return *default* if there is no `Constructs` object.

:Returns:

    out:
        The `Constructs` object. If unset then return *default* if provided.

**Examples**

>>> c = f._get_constructs()
>>> c = f._get_constructs(None)

        '''
        raise NotImplementedError()
    #--- End: def
    
    def array_constructs(self, copy=False):
        return self._get_constructs().array_constructs(copy=copy)
 
    def construct_axes(self, id=None):
        '''Return the identifiers of the domain axes spanned by the construct
data arrays.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    id: `str`
        The identifier of the construct.

:Returns:

    out: `tuple` or `None`
        The identifiers of the domain axes spanned by the construct's
        data array. If the construct does not have a data array then
        `None` is returned.

**Examples**

>>> f.construct_axes('auxiliarycoordinate0')
('domainaxis1', 'domainaxis0')
>>> print(f.construct_axes('auxiliarycoordinate99'))
None

        '''
        return self._get_constructs().construct_axes(id=id)
    #--- End: def
    
    def construct_type(self, id):
        '''TODO
        '''                
        return self._get_constructs().construct_type(id)
    #--- End: def
    
    def constructs(self, copy=False):
        '''Return metadata constructs.

.. versionadded:: 1.7

.. seealso:: `construct_axes`

:Parameters:

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO

        '''
        return self._get_constructs().constructs(copy=copy)
    #--- End: def
    
    @abc.abstractmethod
    def del_construct(self, id):
        '''Remove a construct.

.. versionadded:: 1.7

.. seealso:: `get_construct`, `constructs`

:Parameters:

    id: `str`, optional
        The identifier of the construct.

        *Example:*
          ``id='auxiliarycoordinate0'``
        
:Returns:

    out: 
        The removed construct.

**Examples**

TODO

        '''
        raise NotImplementedError()
    #--- End: def

    def get_construct(self, id):
        '''Return a metadata construct.

:Parameters:

    id: `str`
        TODO

:Returns:

    out:
        TODO

**Examples**

>>> f.constructs()
>>> f.get_construct('dimensioncoordinate1')
<>
>>> f.get_construct('dimensioncoordinate99', 'Not set')
'Not set'
        '''
        return self._get_constructs().get_construct(id)
    #--- End: def

    def domain_axis_name(self, axis):
        '''TODO WHY DO WE NED THIS HERE?
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
#    def set_auxiliary_coordinate(self, item, axes=None, id=None,
#                                 copy=True):
#        '''Set an auxiliary coordinate construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `AuxiliaryCoordinate`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='auxiliarycoordinate0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#
#        '''
#        return self.set_construct('auxiliary_coordinate', item,
#                                  id=id, axes=axes, copy=copy)
#    #--- End: def
#
#    def set_domain_axis(self, domain_axis, id=None, copy=True):
#        '''Set a domain axis construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`
#
#:Parameters:
#
#    item: `DomainAxis`
#        TODO
#        
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='domainaxis2'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#
#        '''
#        return self.set_construct('domain_axis', domain_axis, id=id,
#                                  copy=copy)
#    #--- End: def
#
#    def set_domain_ancillary(self, item, axes=None, id=None, copy=True):
##                             extra_axes=0, copy=True):
#        '''Set a domain ancillary construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `DomainAncillary`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1', 'domainaxis0']``
#        
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='domainancillary0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#
#        ''' 
#        return self.set_construct('domain_ancillary', item, id=id,
#                                  axes=axes, #extra_axes=extra_axes,
#                                  copy=copy)
#    #--- End: def

    def set_construct(self, construct_type, construct, id=None,
                      axes=None, #replace=True,
                      copy=True):
        '''Set a metadata construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: 
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data
        array. Ignored for constructs that can not have a data array,
        i.e. domain axis, cell method and coordinate reference
        constructs.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='cellmeasure0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        '''
        return self._get_constructs().set_construct(construct_type,
                                                    construct, key=id,
                                                    axes=axes,
#                                                    extra_axes=extra_axes,
#                                                    replace=replace,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, id, axes):
        '''Set the domain axes spanned by a construct data array.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct`

:Parameters:

    id: `str`
        The identifier of the construct.

        *Example:*
          ``id='cellmeasure0'``
        
     axes: sequence of `str`
        The identifiers of the domain axes spanned by the data array.

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

:Returns:

    `None`

**Examples**

TODO

        '''
        return self._get_constructs().set_construct_axes(id, axes)
    #--- End: def

#    def set_cell_measure(self, item, axes=None, id=None, copy=True):
#        '''Set a cell measure construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `CellMeasure`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='cellmeasure0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#        '''
#        return self.set_construct('cell_measure', item, id=id,
#                                  axes=axes, copy=copy)
#    #--- End: def
#
#    def set_coordinate_reference(self, item, id=None, copy=True):
#        '''Set a coordinate reference construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `CoordinateReference`
#        TODO
#
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='coordinatereference0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#
#        '''
#        return self.set_construct('coordinate_reference',
#                                  item, id=id, copy=copy)
#    #--- End: def
#
#    def set_dimension_coordinate(self, item, axes=None, id=None,
#                                 copy=True):
#        '''Set a dimension coordinate construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `DimensionCoordinate`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    id: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``id='dimensioncoordinate1'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples**
#
#TODO
#
#        '''
#        return self.set_construct('dimension_coordinate', item, id=id,
#                                  axes=axes, copy=copy)
#    #--- End: def

#--- End: class
