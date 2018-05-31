import abc

import abstract
import mixin

from .constructs import Constructs


class Field(mixin.ConstructAccess, abstract.PropertiesData):
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

        if source is not None:
            try:
                constructs = source._get_constructs(None)
            except AttributeError:
                constructs = None
                
            try:
                data_axes = source.get_data_axes(None)
            except AttributeError:
                data_axes = None
                
            try:
                data = source.get_data(None) 
            except AttributeError:
                data = None

            if data is not None:
                if _use_data:
                    self.set_data(data, data_axes, copy=copy)
            elif data_axes is not None:
                self.set_data_axes(data_axes)
                
            if constructs is not None and (copy or not _use_data):
                constructs = constructs.copy(data=_use_data)
        else:
            constructs = self._Constructs(**self._construct_key_base)

        self._set_component('constructs', None, constructs)
    #--- End: def
    
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        return self._get_component('constructs', None, *default)
    #--- End: def
    
    @property
    def domain(self):
        '''
'''
        return self._Domain(_view_constructs=self._get_constructs())
    #--- End:: def
    
    def cell_methods(self, copy=False):
        return self._get_constructs().constructs('cell_method', copy=copy)
    
    def del_data_axes(self):
        '''
        '''
        return self._del_component('data_axes')
    #--- End: def

    def get_domain(self, copy=True):
        '''
        '''
        return self._Domain(source=self._get_constructs(), copy=copy)
    #--- End: def

    def get_data_axes(self, *default):
        '''Return the domain axes corresponding to the data array dimensions.
        
.. seealso:: `del_data_axes`, `get_data`, `set_data_axes`

:Examples 1:

>>> d = f.get_data_axes()

:Parameters:

    default: optional
        Return *default* if data axes have not been set.

:Returns:

    out: `tuple` 
        The ordered axes of the data array. If there are no data axes
        then return the value of *default* parameter, if provided.

:Examples 2:

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
        return self._get_component('data_axes', None, *default)
    #--- End: def
    
    def field_ancillaries(self, copy=False):
        '''
        '''
        return self._get_constructs().constructs('field_ancillary', copy=copy)

    def del_construct(self, key):
        '''
        '''
        if key in self.domain_axes():
            domain_axis = True
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
        
        x = self.domain.del_construct(key)
        if x is None:
            x = self._get_constructs().del_construct(key)
            
        return x
    #--- End: def

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
            
        self._set_component('data_axes', None, tuple(value))
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

    def del_data(self):
        '''

        '''
        return super(Field, self).del_data()
    #--- End: def

#--- End: class
