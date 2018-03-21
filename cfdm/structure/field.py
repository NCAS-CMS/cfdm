import abc

import abstract
import mixin

from .constructs import Constructs

# ====================================================================
#
# Field object
#
# ====================================================================

class Field(mixin.DomainConstructMethods, abstract.PropertiesData):
    '''A CF field construct.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to some
element of the CF field construct and the field constructs completely
contain all the data and metadata which can be extracted from the file
using the CF conventions.

The field construct consists of a data array (stored in a `Data`
object) and the definition of its domain, ancillary metadata fields
defined over the same domain (stored in `FieldAncillary` objects), and
cell methods constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain
(stored in `CellMethod` objects).

The domain is defined collectively by various other constructs
included in the field:

====================  ================================================
Domain construct      Description
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

All of the constructs contained by the field construct are optional.

The field construct also has optional properties to describe aspects
of the data that are independent of the domain. These correspond to
some netCDF attributes of variables (e.g. units, long_name and
standard_name), and some netCDF global file attributes (e.g. history
and institution).

**Miscellaneous**

Field objects are picklable.

    '''
    __metaclass__ = abc.ABCMeta

    # Define the base of the identity keys for each construct type
    _construct_key_base = {'auxiliary_coordinate': 'auxiliarycoordinate',
                           'cell_measure'        : 'cellmeasure',
                           'cell_method'         : 'cellmethod',
                           'coordinate_reference': 'coordinatereference',
                           'dimension_coordinate': 'dimensioncoordinate',
                           'domain_ancillary'    : 'domainancillary',
                           'domain_axis'         : 'domainaxis',
                           'field_ancillary'     : 'fieldancillary',
    }
    
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        obj._Constructs = Constructs
        return obj
    #--- End: def

    def __init__(self, properties={}, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Provide the new field with descriptive properties.

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super(Field, self).__init__(properties=properties,
                                    source=source, copy=copy,
                                    _use_data=False)
        
        data_axes  = None
        data       = None
        constructs = None
  
        if source is not None and isinstance(source, Field):
            constructs = source._get_constructs(None)
            if constructs is not None and (copy or not _use_data):
                constructs = constructs.copy(data=_use_data)

            data_axes = source.get_data_axes(None)
            data      = source.get_data(None) 
        else:
#            key_base = self._construct_key_base
            constructs = self._Constructs(**self._construct_key_base)
#                auxiliary_coordinate = key_base['auxiliary_coordinate'],
#                dimension_coordinate = key_base['dimension_coordinate'],
#                cell_measure         = key_base['cell_measure'],
#                domain_ancillary     = key_base['domain_ancillary'],
#                field_ancillary      = key_base['field_ancillary'],
#                coordinate_reference = key_base['coordinate_reference'],
#                domain_axis          = key_base['domain_axis'],
#                cell_method          = key_base['cell_method'],
#           )

        self._set_component(3, 'constructs', None, constructs)

        if data is not None:
            self.set_data(data, data_axes, copy=copy)
        elif data_axes is not None:
            self.set_data_axes(data_axes)
    #--- End: def
    
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        return self._get_component(3, 'constructs', None, *default)
    #--- End: def
    
#    def array_constructs(self, copy=False):
#        return self._get_constructs().array_constructs(copy=copy)
#    
#    def auxiliary_coordinates(self, copy=False):
#        return self._get_constructs().constructs('auxiliary_coordinate', copy=copy)
#    
#    def cell_measures(self, copy=False):
#        return self._get_constructs().constructs('cell_measure', copy=copy)
    
    def cell_methods(self, copy=False):
        return self._get_constructs().constructs('cell_method', copy=copy)
    
#    def construct_axes(self, key=None):
#        return self._get_constructs().construct_axes(key=key)
#    
#    def construct_type(self, key):
#        return self._get_constructs().construct_type(key)
#    
#    def construct(self, construct, copy=False):
#        '''
#        '''
#        c = self._get_constructs().constructs(copy=False)[construct]
#        if copy:
#            c = c.copy()
#
#        return c
#    #--- End: def
        
#    def constructs(self, copy=False):
#        '''Return all of the data model constructs of the field.
#
#.. versionadded:: 1.6
#
#.. seealso:: `dump`
#
#:Examples 1:
#
#>>> f.{+name}()
#
#:Returns:
#
#    out: `list`
#        The objects correposnding CF data model constructs.
#
#:Examples 2:
#
#>>> print f
#eastward_wind field summary
#---------------------------
#Data           : eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1
#Cell methods   : time: mean
#Axes           : time(1) = [2057-06-01T00:00:00Z] 360_day
#               : air_pressure(15) = [1000.0, ..., 10.0] hPa
#               : latitude(72) = [88.75, ..., -88.75] degrees_north
#               : longitude(96) = [1.875, ..., 358.125] degrees_east
#>>> f.{+name}()
#[<Field: eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1>,
# <DomainAxis: 96>,
# <DomainAxis: 1>,
# <DomainAxis: 15>,
# <DomainAxis: 72>,
# <CellMethod: dim3: mean>,
# <DimensionCoordinate: longitude(96) degrees_east>,
# <DimensionCoordinate: time(1) 360_day>,
# <DimensionCoordinate: air_pressure(15) hPa>,
# <DimensionCoordinate: latitude(72) degrees_north>]
#
#        '''
#        return self._get_constructs().constructs(copy=copy)
#    #--- End: def
    
#    def coordinate_references(self, copy=False):
#        return self._get_constructs().constructs('coordinate_reference', copy=copy)
#    
#    def coordinates(self, copy=False):
#        '''
#        '''
#        out = self.dimension_coordinates(copy=copy)
#        out.update(self.auxiliary_coordinates(copy=copy))
#        return out
#    #--- End: def

    def del_data_axes(self):
        '''
        '''
        return self._del_component(1, 'data_axes')
    #--- End: def
      
#    def get_construct(self, key, *default):
#        '''
#        '''
#        return self._get_constructs().get_construct(key, *default)
#    #--- End: def

    def get_domain(self):
        '''
        '''
        return self._Domain(constructs=self._get_constructs())
    #--- End: def

    def get_data_axes(self, *default):
        '''Return the domain axes for the data array dimensions.
        
.. seealso:: `axes`, `axis`, `item_axes`

:Examples 1:

>>> d = f.{+name}()

:Returns:

    out: list or None
        The ordered axes of the data array. If there is no data array
        then `None` is returned.

:Examples 2:

>>> f.ndim
3
>>> f.{+name}()
['dim2', 'dim0', 'dim1']
>>> f.del_data()
>>> print f.{+name}()
None

>>> f.ndim
0
>>> f.{+name}()
[]

        '''    
        return self._get_component(1, 'data_axes', None, *default)
    #--- End: def
    
#    def dimension_coordinates(self, copy=False):
#        return self._get_constructs().constructs('dimension_coordinate', copy=copy)
#    
#    def domain_ancillaries(self, copy=False):
#        return self._get_constructs().constructs('domain_ancillary', copy=copy)
#    
#    def domain_axes(self, copy=False):
#        return self._get_constructs().domain_axes(copy=copy)
#    
#    def domain_axis_name(self, axis):
#        '''
#        '''
#        return self._get_constructs().domain_axis_name(axis)
#    #--- End: for
    
    def field_ancillaries(self, copy=False):
        return self._get_constructs().constructs('field_ancillary', copy=copy)

    def del_construct(self, key):
        '''
        '''
        if key in self.domain_axes():
            if key in self.get_data_axes(()):
                raise ValueError(
"Can't remove domain axis {!r} that is spanned by the field's data".format(key))

            # Remove reference to removed domain axis construct in
            # cell method constructs
            for cm_key, cm in self.cell_methods().iteritems():
                axes = cm.get_axes()
                if key not in axes:
                    continue
            
                axes = list(axes)
                axes.remove(key)
                cm.set_axes(axes)
        #--- End: if

        return super(Field, self).del_construct(key)
    #--- End: def

#    def set_auxiliary_coordinate(self, item, key=None, axes=None,
#                                 copy=True, replace=True):
#        '''Insert an auxiliary coordinate object into the {+variable}.
#
#.. seealso:: `set_domain_axis`, `set_measure`, `set_data`,
#             `set_dim`, `set_ref`
#
#:Parameters:
#
#    item: `AuxiliaryCoordinate`
#        The new auxiliary coordinate object. If it is not already a
#        auxiliary coordinate object then it will be converted to one.
#
#    key: `str`, optional
#        The identifier for the *item*. By default a new, unique
#        identifier will be generated.
#
#    axes: sequence of `str`, optional
#        The ordered list of axes for the *item*. Each axis is given by
#        its identifier. By default the axes are assumed to be
#        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
#        axes spanned by the *item*.
#
#    {+copy_item_in}
#      
#    replace: `bool`, optional
#        If False then do not replace an existing auxiliary coordinate
#        object of domain which has the same identifier. By default an
#        existing auxiliary coordinate object with the same identifier
#        is replaced with *item*.
#    
#:Returns:
#
#    out: `str`
#        The identifier for the inserted *item*.
#
#:Examples:
#
#>>>
#
#        '''
#        if not replace and key in self.auxiliary_coordinates():
#            raise ValueError(
#"Can't insert auxiliary coordinate object: Identifier {!r} already exists".format(key))
#
#        return self.set_construct('auxiliary_coordinate', item,
#                                  key=key, axes=axes, copy=copy)
#    #--- End: def

    def set_data(self, data, axes, copy=True):
        '''Insert a data array into the {+variable}.

:Examples 1:

>>> f.set_data(d)

:Parameters:

    data: `Data`
        The data array to be inserted.

    axes: sequence of `str`
        A list of axis identifiers (``'dimN'``), stating the axes, in
        order, of the data array.

        The ``N`` part of each identifier should be replaced by an
        integer greater then or equal to zero such that either a) each
        axis identifier is the same as one in the field's domain, or
        b) if the domain has no axes, arbitrary integers greater then
        or equal to zero may be used, the only restriction being that
        the resulting identifiers are unique.

        If an axis of the data array already exists in the domain then
        the it must have the same size as the domain axis. If it does
        not exist in the domain then a new axis will be created.

        By default the axes will either be those defined for the data
        array by the domain or, if these do not exist, the domain axis
        identifiers whose sizes unambiguously match the data array.

    copy: `bool`, optional
        If False then the new data array is not deep copied prior to
        insertion. By default the new data array is deep copied.

    replace: `bool`, optional
        If False then raise an exception if there is an existing data
        array. By default an existing data array is replaced with
        *data*.
   
:Returns:

    `None`

:Examples 2:

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.set_data(Data([[0, 1, 2]]))

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.set_data(Data([[0, 1, 2]]), axes=['dim0', 'dim1'])

>>> f.axes()
{}
>>> f.set_data(Data([[0, 1], [2, 3, 4]]))
>>> f.axes()
{'dim0': 2, 'dim1': 3}

>>> f.set_data(Data(4))

>>> f.set_data(Data(4), axes=[])

>>> f.axes()
{'dim0': 3, 'dim1': 2}
>>> data = Data([[0, 1], [2, 3, 4]])
>>> f.set_data(data, axes=['dim1', 'dim0'], copy=False)

>>> f.set_data(Data([0, 1, 2]))
>>> f.set_data(Data([3, 4, 5]), replace=False)
ValueError: Can't initialize data: Data already exists
>>> f.set_data(Data([3, 4, 5]))

        '''
        if axes is not None:
            self.set_data_axes(axes)

        super(Field, self).set_data(data, copy=copy)
    #--- End: def

    def set_data_axes(self, value):
        '''
        '''
        domain_axes = self.domain_axes()
        for axis in value:
            if axis not in domain_axes:
                raise ValueError("Can't set data axes: Domain axis {!r} doesn't exist".format(axis))
            
        self._set_component(1, 'data_axes', None, tuple(value))
    #--- End: def
    
#    def cell_methods(self, copy=False):
#        '''
#        '''
#        out = self.Constructs.cell_methods(copy=copy)
#
#        if not description:
#            return self.Constructs.cell_methods()
#        
#        if not isinstance(description, (list, tuple)):
#            description = (description,)
#            
#        cms = []
#        for d in description:
#            if isinstance(d, dict):
#                cms.append([self._CellMethod(**d)])
#            elif isinstance(d, basestring):
#                cms.append(self._CellMethod.parse(d))
#            elif isinstance(d, self._CellMethod):
#                cms.append([d])
#            else:
#                raise ValueError("asd 123948u m  BAD DESCRIPTION TYPE")
#        #--- End: for
#
#        keys = self.cell_methods().keys()                    
#        f_cell_methods = self.cell_methods().values()
#        nf = len(f_cell_methods)
#
#        out = {}
#        
#        for d in cms:
#            c = self._conform_cell_methods(d)
#
#            n = len(c)
#            for j in range(nf-n+1):
#                found_match = True
#                for i in range(0, n):
#                    if not f_cell_methods[j+i].match(c[i].properties()):
#                        found_match = False
#                        break
#                #--- End: for
#            
#                if not found_match:
#                    continue
#
#                # Still here?
#                key = tuple(keys[j:j+n])
#                if len(key) == 1:
#                    key = key[0]
#
#                if key not in out:
#                    value = f_cell_methods[j:j+n]
#                    if copy:
#                    value = [cm.copy() for cm in value]                        
#
#                out[key] = value
#            #--- End: for
#        #--- End: for
#        
#        return out
#    #--- End: def
    
    def set_cell_method(self, cell_method, key=None, copy=True):
        '''Insert cell method objects into the {+variable}.

.. seealso:: `set_aux`, `set_measure`, `set_ref`,
             `set_data`, `set_dim`

:Parameters:

    cell_method: `CellMethod`

:Returns:

    `None`

:Examples:

        '''
        self.set_construct('cell_method', cell_method, key=key,
                           copy=copy)
    #--- End: def

#    def set_domain_axis(self, domain_axis, key=None, replace=True, copy=True):
#        '''Insert a domain axis into the {+variable}.
#
#.. seealso:: `set_aux`, `set_measure`, `set_ref`,
#             `set_data`, `set_dim`
#
#:Parameters:
#
#    axis: `DomainAxis`
#        The new domain axis.
#
#    key: `str`, optional
#        The identifier for the new axis. By default a new,
#        unique identifier is generated.
#  
#    replace: `bool`, optional
#        If False then do not replace an existing axis with the same
#        identifier but a different size. By default an existing axis
#        with the same identifier is changed to have the new size.
#
#:Returns:
#
#    out: `str`
#        The identifier of the new domain axis.
#
#
#:Examples:
#
#>>> f.set_domain_axis(DomainAxis(1))
#>>> f.set_domain_axis(DomainAxis(90), key='dim4')
#>>> f.set_domain_axis(DomainAxis(23), key='dim0', replace=False)
#
#        '''
#        axes = self.domain_axes()
#        if not replace and key in axes and axes[key].size != domain_axis.size:
#            raise ValueError(
#"Can't insert domain axis: Existing domain axis {!r} has different size (got {}, expected {})".format(
#    key, domain_axis.size, axes[key].size))
#
#        return self.set_construct('domain_axis',
#                                  domain_axis, key=key, copy=copy)
#    #--- End: def

    def set_field_ancillary(self, construct, key=None, axes=None,
                            copy=True, replace=False):
        '''Insert a field ancillary object into the {+variable}.
        
    {+copy_item_in}
      
        '''
        if replace:
            if key is None:
                raise ValueError("Must specify which construct to replace")

            return self._get_constructs().replace(construct, key, axes=axes,
                                                 copy=copy)
        #--- End: if
        
        return self.set_construct('field_ancillary', construct,
                                  key=key, axes=axes,
                                  copy=copy)
    #--- End: def

#    def set_domain_ancillary(self, item, key=None, axes=None,
#                                copy=True, replace=True):
#        '''Insert a domain ancillary object into the {+variable}.
#      
#    {+copy_item_in}
#        '''       
#        if not replace and key in self.domain_ancillaries():
#            raise ValueError(
#"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))
#
#        return self.set_construct('domain_ancillary', item, key=key,
#                                  axes=axes,
#                                  copy=copy)
#    #--- End: def
#
#    def set_construct(self, construct_type, construct, key=None, axes=None,
#                      copy=True):
#        '''
#        '''
#        return self._get_constructs().set_construct(construct_type,
#                                                    construct,
#                                                    key=key,
#                                                    axes=axes,
#                                                    copy=copy)
#    #--- End: def
#
#    def set_construct_axes(self, key, axes):
#        '''
#        '''
#        return self._get_constructs().set_construct_axes(key, axes)
#    #--- End: def
#
#    def set_cell_measure(self, item, key=None, axes=None, copy=True, replace=True):
#        '''Insert a cell measure object into the {+variable}.
#
#.. seealso:: `set_domain_axis`, `set_aux`, `set_data`,
#             `set_dim`, `set_ref`
#
#:Parameters:
#
#    item: `CellMeasure`
#        The new cell measure object.
#
#    key: `str`, optional
#        The identifier for the *item*. By default a new, unique
#        identifier will be generated.
#
#    axes: sequence of `str`, optional
#        The ordered list of axes for the *item*. Each axis is given by
#        its identifier. By default the axes are assumed to be
#        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
#        axes spanned by the *item*.
#
#    {+copy_item_in}
#      
#    replace: `bool`, optional
#        If False then do not replace an existing cell measure object
#        of domain which has the same identifier. By default an
#        existing cell measure object with the same identifier is
#        replaced with *item*.
#    
#:Returns:
#
#    out: 
#        The identifier for the *item*.
#
#:Examples:
#
#>>>
#
#        '''
#        if not replace and key in self.cell_measures():
#            raise ValueError(
#"Can't insert cell measure object: Identifier {0!r} already exists".format(key))
#
#        return self.set_construct('cell_measure', item, key=key,
#                                  axes=axes, copy=copy)
#    #--- End: def
#
#    def set_coordinate_reference(self, item, key=None, axes=None,
#                                    copy=True, replace=True):
#        '''Insert a coordinate reference object into the {+variable}.
#
#.. seealso:: `set_domain_axis`, `set_aux`, `set_measure`,
#             `set_data`, `set_dim`
#             
#:Parameters:
#
#    item: `CoordinateReference`
#        The new coordinate reference object.
#
#    key: `str`, optional
#        The identifier for the *item*. By default a new, unique
#        identifier will be generated.
#
#    axes: *optional*
#        *Ignored*
#
#    {+copy_item_in}
#
#    replace: `bool`, optional
#        If False then do not replace an existing coordinate reference object of
#        domain which has the same identifier. By default an existing
#        coordinate reference object with the same identifier is replaced with
#        *item*.
#    
#:Returns:
#
#    out: 
#        The identifier for the *item*.
#
#
#:Examples:
#
#>>>
#
#        '''
#        return self.set_construct('coordinate_reference',
#                                  item, key=key, copy=copy)
#    #--- End: def
#
#    def set_dimension_coordinate(self, item, key=None, axes=None, copy=True, replace=True):
#        '''Insert a dimension coordinate object into the {+variable}.
#
#.. seealso:: `set_aux`, `set_domain_axis`, `set_item`,
#             `set_measure`, `set_data`, `set_ref`,
#             `remove_item`
#
#:Parameters:
#
#    item: `DimensionCoordinate` or `cf.Coordinate` or `cf.AuxiliaryCoordinate`
#        The new dimension coordinate object. If it is not already a
#        dimension coordinate object then it will be converted to one.
#
#    axes: sequence of `str`, optional
#        The axis for the *item*. The axis is given by its domain
#        identifier. By default the axis will be the same as the given
#        by the *key* parameter.
#
#    key: `str`, optional
#        The identifier for the *item*. By default a new, unique
#        identifier will be generated.
#
#    {+copy_item_in}
#
#    replace: `bool`, optional
#        If False then do not replace an existing dimension coordinate
#        object of domain which has the same identifier. By default an
#        existing dimension coordinate object with the same identifier
#        is replaced with *item*.
#    
#:Returns:
#
#    out: 
#        The identifier for the inserted *item*.
#
#:Examples:
#
#>>>
#
#        '''
#        if not replace and key in self.dimension_coordinates():
#            raise ValueError(
#"Can't insert dimension coordinate object: Identifier {!r} already exists".format(key))
#
#        return self.set_construct('dimension_coordinate',
#                                  item, key=key, axes=axes, copy=copy)
#    #--- End: def

    def del_data(self):
        '''

        '''
        return super(Field, self).del_data()
    #--- End: def

#--- End: class
