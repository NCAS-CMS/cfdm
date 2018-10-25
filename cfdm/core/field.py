from builtins import super

from . import abstract
from . import mixin

from . import Constructs


class Field(mixin.ConstructAccess, abstract.PropertiesData):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.ConstructAccess, abstract.PropertiesData), {}))):
    '''A CF field construct.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to a field
construct or some element of the CF field construct. The field
construct contains all the data and metadata which can be extracted
from the file using the CF conventions.

The field construct consists of a data array (stored in a `Data`
object) and the definition of its domain, ancillary metadata fields
defined over the same domain (stored in `FieldAncillary` objects), and
cell methods constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain
(stored in `CellMethod` objects).

The domain is implied by other types of construct included in the
field:

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

    '''

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
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance
    
#        obj = object.__new__(cls, *args, **kwargs)
#        obj._Constructs = Constructs
#        return obj
    #--- End: def

    def __init__(self, properties={}, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

If the source parameter contains a data array then it will be copied
into the new field, otherwise the data must be set after
initialisation with the `set_data` method.
        
:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Example:*
           ``properties={'standard_name': 'altitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    source: optional 
        Override the *properties* parameter with
        ``source.properties()``.

        If *source* does not have this method, or it can not return
        anything, then the *properties* parameter is not set.

        In addition, if *source* has any of a data array, data array
        axes, and metadata constructs then these are copied to the new
        field.

        *Example:*
          If ``g`` is a `Field` object then ``f = Field(source=g)``
          is equivalent to ``f = g.copy()``.

        *Example:*
          If ``dc`` is a `DimensionCoordinate` object then

                >>> f = Field(source=dc)

          is equivalent to

             >>> f = Field(properties=dc.properties())
             >>> f.set_data(dc.get_data(None))

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization By default parameters are deep copied.

        '''
        super().__init__(properties=properties, source=source,
                         copy=copy, _use_data=False)

        if source is not None:
            # Initialise constructs and the data from the source
            # parameter
            try:
                constructs = source._get_constructs(None)
            except AttributeError:
                constructs = None
                
            try:
                data = source.get_data(None) 
            except AttributeError:
                data = None

            try:
                data_axes = source.get_data_axes(None)
            except AttributeError:
                data_axes = None
                                
            if constructs is not None and (copy or not _use_data):
                constructs = constructs.copy(data=_use_data)

#            if data is not None:
 #               if _use_data:
 #                   self.set_data(data, data_axes, copy=copy)
 #           elif data_axes is not None:
 #               self.set_data_axes(data_axes)
        else:
            constructs = None
            data       = None
            data_axes  = None

        if constructs is None:
            constructs = self._Constructs(**self._construct_key_base)
            
        self._set_component('constructs', constructs, copy=False)

        if data is not None and _use_data:
            self.set_data(data, data_axes, copy=copy)
        elif data_axes is not None:
            self.set_data_axes(data_axes)
     #--- End: def
    
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
    # Attributes
    # ----------------------------------------------------------------
    @property
    def domain(self):
        '''Return the domain.
        
``f.domain`` is equivalent to ``f.get_domain()`` 

.. versionadded:: 1.7

.. seealso:: `get_domain`

:Returns:

    out: `Domain`

**Examples**

>>> d = f.domain
TODO
        '''
        return self.get_domain()
    #--- End: def
    
    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
#    def cell_methods(self, copy=False):
#        '''Return the cell method constructs.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`
#
#:Parameters:
#
#    copy: `bool`, optional
#        If `True` then deep copies of the constructs are returned.
#
#:Returns:
#
#    out: `OrderDict`
#
#**Examples**
#
#>>> f.cell_methods()
#OrderedDict([('cellmethod0',
#              <CellMethod: domainaxis2: mean (interval: 1 day comment: ok)>),
#             ('cellmethod1', <CellMethod: domainaxis1: maximum where sea>)])
#
#        '''
#        return self._get_constructs().constructs(
#            construct_type='cell_method', copy=copy)
#    #--- End: def
    
    def del_data_axes(self, *default):
        '''Remove the identifiers of the domain axes spanned by the data
array.

.. versionadded:: 1.7

.. seealso:: `data`, `get_data_axes`, `set_data_axes`

:Parameters:

    default: optional
        Return *default* if data axes have not been set.

:Returns:

    out: `tuple` 
        The removed identifiers of the domain axes spanned by the data
        array. If unset then *default* is returned, if provided.

**Examples**

TODO

        '''
        return self._del_component('data_axes', *default)
    #--- End: def

    def get_domain(self):
        '''Return the domain.

.. versionadded:: 1.7

.. seealso:: `domain`

:Returns:

    out: `Domain`

**Examples**

>>> d = f.get_domain()
TODO
        '''
        return self._Domain.fromconstructs(self._get_constructs())
    #--- End: def

    def get_data_axes(self, *default):
        '''Return the identifiers of the domain axes spanned by the data
array.

.. versionadded:: 1.7

.. seealso:: `data`, `del_data_axes`, `get_data`, `set_data_axes`

:Parameters:

    default: optional
        Return *default* if data axes have not been set.

:Returns:

    out: `tuple` 
        The identifiers of the domain axes spanned by the data
        array. If unset then *default* is returned, if provided.

**Examples**

>>> f.ndim
3
>>> f.get_data_axes()
('dim2', 'dim0', 'dim1')
>>> d = f.del_data()
>>> print f.get_data_axes(None)
None

>>> f.ndim
0
>>> f.get_data_axes()
()

        '''    
        return self._get_component('data_axes', *default)
    #--- End: def
    
#    def field_ancillaries(self, copy=False):
#        '''Return the field ancillary constructs.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`
#
#:Parameters:
#
#    copy: `bool`, optional
#        If `True` then deep copies of the constructs are returned.
#
#:Returns:
#
#    out: `dict`
#        TODO
#
#**Examples**
#
#>>> f.field_ancillaries()
#TODO
#
#
#'''
#        return self._get_constructs().constructs(
#            construct_type='field_ancillary', copy=copy)

    def del_construct(self, id):
        '''Remove a construct.

If a removed domain axis construct is referenced by a cell method
construct, then that reference is also removed.

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
        if id in self.domain_axes():
            domain_axis = True
            if id in self.get_data_axes(()):
                raise ValueError(
"Can't remove domain axis {!r} that is spanned by the field's data".format(id))

            # Remove reference to removed domain axis construct in
            # cell method constructs
            for cm_key, cm in self.cell_methods().items():
                axes = cm.get_axes()
                if id not in axes:
                    continue
                
                axes = list(axes)
                axes.remove(id)
                cm.set_axes(axes)
        #--- End: if
        
        x = self.domain.del_construct(id)
        if x is None:
            x = self._get_constructs().del_construct(id)
            
        return x
    #--- End: def

    def set_data(self, data, axes, copy=True):
        '''Set the data.

The units, calendar and fill value properties of the data object are
removed prior to insertion.

.. versionadded:: 1.7

.. seealso:: `data`, `del_data`, `get_data`, `has_data`, `set_data_axes`

:Parameters:

    data: `Data`
        The data to be inserted.

    axes: sequence of `str` or `None`, optional
        The identifiers of the domain axes spanned by the data
        array. If `None` then the data axes are not set.

        The axes may also be set afterwards with the `set_data_axes`
        method.

    copy: `bool`, optional
        If False then do not copy the data prior to insertion. By
        default the data are copied.

:Returns:

    `None`

**Examples**

TODO

        '''
        if axes is not None:
            self.set_data_axes(axes)

        super().set_data(data, copy=copy)
    #--- End: def

    def set_data_axes(self, value):
        '''Set the identifiers of the domain axes spanned by the data array.

.. versionadded:: 1.7

.. seealso:: `data`, `del_data_axes`, `get_data`, `get_data_axes`

:Parameters:

    value: sequence of `str`
        The identifiers of the domain axes spanned by the data array.

:Returns:

    `None`

**Examples**

TODO

        '''
        domain_axes = self.domain_axes()
        for axis in value:
            if axis not in domain_axes:
                raise ValueError(
"Can't set data axes: Domain axis {!r} doesn't exist".format(axis))
            
        self._set_component('data_axes', tuple(value), copy=False)
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
    
    def set_cell_method(self, cell_method, id=None, copy=True):
        '''Set a cell method construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `CellMethod`
        TODO
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='cellmethod0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        '''
        self.set_construct('cell_method', cell_method, id=id,
                           copy=copy)
    #--- End: def

    def set_field_ancillary(self, construct, axes=None, id=None,
                            copy=True):
        '''Set a field ancillary construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `FieldAncillary`
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data array.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='fieldancillary0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO
        
        '''
        return self.set_construct('field_ancillary', construct, id=id,
                                  axes=axes, copy=copy)
    #--- End: def

#--- End: class
