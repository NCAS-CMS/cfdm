from builtins import object
from future.utils import with_metaclass

import abc


class ConstructAccess(with_metaclass(abc.ABCMeta, object)):
    '''Mixin class for accessing an embedded `Constructs` object.

.. versionadded:: 1.7.0

    '''   
    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''Return the `Constructs` object

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        If set then return *default* if there is no `Constructs` object.

:Returns:

    out:
        The `Constructs` object. If unset then return *default* if provided.

**Examples:**

>>> c = f._get_constructs()
>>> c = f._get_constructs(None)

        '''
        raise NotImplementedError()
    #--- End: def
    
    def array_constructs(self, copy=False):
        return self._get_constructs().array_constructs(copy=copy)
 
    def construct_axes(self, cid=None):
        '''Return the domain axes spanned by metadata construct data arrays.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    cid: `str`
        The identifier of the construct.

:Returns:

    out: `tuple` or `None`

        The identifiers of the domain axes constructs spanned by data
        array of metadata constructs. If a metadata construct does not have a
        data array then `None` is returned.

**Examples:**

>>> f.construct_axes('auxiliarycoordinate0')
('domainaxis1', 'domainaxis0')
>>> print(f.construct_axes('auxiliarycoordinate99'))
None

        '''
        return self._get_constructs().construct_axes(cid=cid)
    #--- End: def
    
    def construct_type(self, cid):
        '''TODO

.. versionadded:: 1.7.0
        '''                
        return self._get_constructs().construct_type(cid)
    #--- End: def
    
    def constructs(self, construct_type=None, copy=False):
        '''Return metadata constructs.

.. versionadded:: 1.7.0

.. seealso:: `del_construct`, `get_construct`, `get_construct_axes`,
             `get_construct_id`, `has_construct`, `set_construct`

:Parameters:

    construct_type: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct_type*            Constructs
          ==========================  ================================
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.
        
        If cell method contructs, and no other construct types, have
        been selected with the *construct_type* parameter then the
        constructs are returned in an ordered dictionary
        (`collections.OrderedDict`). The order is determined by the
        order in which the cell method constructs were originally
        added.

**Examples:**

>>> f.constructs()
{}

>>> f.constructs()
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
 'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
 'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>,
 'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
 'domainaxis0': <DomainAxis: 1>,
 'domainaxis1': <DomainAxis: 10>,
 'domainaxis2': <DomainAxis: 9>,
 'domainaxis3': <DomainAxis: 1>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
>>> f.constructs(construct_type='coordinate_reference')
{'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}
>>> f.constructs(construct_type='cell_method')
OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
             ('cellmethod1', <CellMethod: domainaxis3: maximum>)])
>>> f.constructs(construct_type=['cell_method', 'field_ancillary'])
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

        '''
        return self._get_constructs().constructs(construct_type=construct_type,
                                                 copy=copy)
    #--- End: def
    
    @abc.abstractmethod
    def del_construct(self, cid):
        '''Remove a construct.

.. versionadded:: 1.7.0

.. seealso:: `get_construct`, `constructs`

:Parameters:

    cid: `str`, optional
        The identifier of the construct.

        *Example:*
          ``cid='auxiliarycoordinate0'``
        
:Returns:

    out: 
        The removed construct.

**Examples:**

TODO

        '''
        raise NotImplementedError()
    #--- End: def

    def get_construct(self, cid):
        '''Return a metadata construct.

.. versionadded:: 1.7.0

:Parameters:

    cid: `str`
        TODO

:Returns:

    out:
        TODO

**Examples:**

>>> f.constructs()
>>> f.get_construct('dimensioncoordinate1')
<>
>>> f.get_construct('dimensioncoordinate99', 'Not set')
'Not set'
        '''
        return self._get_constructs().get_construct(cid)
    #--- End: def

    def get_construct_axes(self, cid, *default):
        '''Return the domain axes spanned by a metadata construct data array.

.. versionadded:: 1.7.0

.. seealso:: `construct_axes`, `get_construct`, `set_construct_axes`

:Parameters:

    cid: `str`
        The construct identifier of the metadata construct.

        *Example:*
          ``cid='domainancillary1'``

    default: optional
        Return *default* if the metadata construct does not have a
        data array, or no domain axes have been set.

:Returns:

    out:
        The identifiers of the domain axis constructs spanned by data
        array. If a metadata construct does not have a data array, or
        no domain axes have been set, then `None` is returned.

**Examples:**

>>> f.get_construct_axes('domainancillary2')
('domainaxis1', 'domainaxis0')
>>> da = f.get_construct('domainancillary2')
>>> data = da.del_data()
>>> print(f.get_construct_axes('domainancillary2', None))
None

>>> f.get_construct_axes('cellmethod0', 'no axes')
'no axes'

        '''
        axes = self.construct_axes().get(cid)
        if axes is None:
            if default:
                return default[0]

            raise ValueError("no axes.")

        return axes
    #--- End: def
    
    def has_construct(self, cid):
        '''Whether a construct exisits.

.. versionadded:: 1.7.0

:Parameters:

    cid: `str`
        TODO

:Returns:

    out: `bool`
        True if the construct exists, otherwise False.

**Examples:**

TODO
        '''
        return self._get_constructs().has_construct(cid)
    #--- End: def

    def domain_axis_name(self, axis):
        '''TODO WHY DO WE NED THIS HERE?

.. versionadded:: 1.7.0

        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
    def set_construct(self, construct, cid=None, axes=None,
                      copy=True):
        '''Set a metadata construct.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    construct:
        The metadata construct to be inserted.

    axes: sequence of `str`, optional
        The construct identifiers of the domain axis constructs
        spanned by the data array. An exception is raised if used for
        a metadata construct that can not have a data array,
        i.e. domain axis, cell method and coordinate reference
        constructs.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
        *Example:*
          ``axes=['domainaxis1', 'domainaxis0']``
        
    cid: `str`, optional
        The construct identifier to be used for the construct. If not
        set then a new, unique identifier is created automatically. If
        the identifier already exisits then the exisiting construct
        will be replaced.

        *Example:*
          ``cid='cellmeasure0'``

    copy: `bool`, optional
        If True then return a copy of the unique selected
        construct. By default the construct is not copied.
        
:Returns:

     out: `str`
        The construct identifier for the construct.
    
**Examples:**

>>> cid = f.set_construct(c)
>>> cid = f.set_construct(c, copy=False)
>>> cid = f.set_construct(c, axes=['domainaxis2'])
>>> cid = f.set_construct(c, cid='cellmeasure0')

        '''
        return self._get_constructs().set_construct(construct, cid=cid,
                                                    axes=axes,
#                                                    extra_axes=extra_axes,
#                                                    replace=replace,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, cid, axes):
        '''Set the domain axis constructs spanned by a metadata construct data
array.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct`

:Parameters:

    cid: `str`
        The construct identifier of the metadata construct.

        *Example:*
          ``cid='dimensioncoordinate2'``

     axes: sequence of `str`
        The construct identifiers of the domain axis constructs
        spanned by the data array.

        The axes may also be set with the `set_construct` method.

        *Example:*
          ``axes=['domainaxis1']``

        *Example:*
          ``axes=['domainaxis1', 'domainaxis0']``

:Returns:

    `None`

**Examples:**

>>> cid = f.set_construct(c)
>>> f.set_construct_axes(cid, axes=['domainaxis1'])

        '''
        return self._get_constructs().set_construct_axes(cid, axes)
    #--- End: def

#--- End: class
