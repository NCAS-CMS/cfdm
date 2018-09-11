from builtins import str
from builtins import object
class API(object):
    '''
    '''

    @staticmethod
    def copy_field(field):
        '''

:Parameters:

    field: 

:Returns:

    out:

        '''
        return field.copy()
    #--- End: def

    @staticmethod
    def equal_constructs(construct0, construct1, ignore_construct_type=False):
        '''

        '''    
        return construct0.equals(construct1, ignore_construct_type=ignore_construct_type)
    #--- End: def

    @staticmethod
    def equal_datums(coordinate_reference0, coordinate_reference1):
        '''
:Parameters:

    coordinate_reference0: coordinate reference construct

    coordinate_reference1: coordinate reference construct

:Returns:

    out: `bool`
        '''
        datum0 = coordinate_reference0.datum
        datum1 = coordinate_reference1.datum
        return datum0.equals(datum1)
    #--- End: def

    @staticmethod
    def expand_dims(construct, position=0, axis=None, copy=True):
        '''
        '''
        return construct.expand_dims(position=position, axis=axis, copy=copy)
    #--- End: def

    @staticmethod
    def get_array(data):
        '''
        '''
        return data.get_array()
    #--- End: def

    @staticmethod
    def get_auxiliary_coordinates(field):
        '''
        '''
        return field.auxiliary_coordinates()
    #--- End: def

    @staticmethod
    def get_bounds(construct, *default):
        '''
        '''
        return construct.get_bounds(*default)
    #--- End: def

    @staticmethod
    def get_cell_measures(field):
        '''
        '''
        return field.cell_measures()
    #--- End: def
        
    @staticmethod
    def get_cell_methods(field):
        '''
        '''
        return field.cell_methods()
    #--- End: def
       
    @staticmethod
    def get_cell_method_axes(cell_method, *default):
        '''

:Returns:

    out: `tuple`
'''
        return cell_method.get_axes(*default)
    #--- End: for
    
    @staticmethod
    def get_cell_method_string(cell_method):
        '''
:Returns:

    out: `str`
'''
        return str(cell_method)
    #--- End: for

    @staticmethod
    def get_construct_axes(field, key):
        '''
        '''
        return field.construct_axes(key)
    #--- End: def
    
    @staticmethod
    def get_constructs(field, axes=None):
        '''Return constructs that span particular axes.

If no axes are specified then all constructs are returned.

If axes are specified then constructs whose data arrays span those
axes, and possibly other axes, are returned.

        '''
        return field.constructs(axes=axes)
    #--- End: def
    
    @staticmethod
    def get_coordinate_reference_coordinates(coordinate_reference):
        '''Return the coordinates of a coordinate reference object.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `set`

        '''
        return coordinate_reference.coordinates()
    #--- End: def

    @staticmethod
    def get_coordinate_conversion_parameters(coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.coordinate_conversion.parameters()
    #--- End: def

    @staticmethod
    def get_coordinate_references(field):
        '''
        '''
        return field.coordinate_references()
    #--- End: def

    @staticmethod
    def get_coordinates(field):
        '''
        '''
        return field.coordinates()
    #--- End: def

    @staticmethod
    def get_data(parent, *default):
        '''Return the data array.

:Examples 1:

>>> data = w.get_data(x)

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: 
        The data array.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_data(d)
<Data: [-89.5, ..., 89.5] degrees_north>

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data(b)
<Data: [[-90, ..., 90]] degrees_north>
        '''
        return parent.get_data(*default)
    #--- End: def

    @staticmethod
    def get_data_axes(field):
        '''
        '''
        return field.get_data_axes()
    #--- End: def

    @staticmethod
    def get_data_calendar(data, *default):
        '''
        '''
        return data.get_calendar(*default)
    #--- End: def

    @staticmethod
    def get_data_units(data, *default):
        '''
        '''
        return data.get_units(*default)
    #--- End: def

    @staticmethod
    def get_domain_ancillaries(field):
        '''
        '''
        return field.domain_ancillaries()

    @staticmethod
    def get_domain_axes(field):
        '''
        '''
        return field.domain_axes()
        
    @staticmethod
    def get_domain_axis_size(field, axis):
        '''
        '''
        return field.domain_axes()[axis].get_size()

    @staticmethod
    def get_datum(coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.datum
    #--- End: def

    @staticmethod
    def get_datum_parameters(ref):
        '''Return the parameter-valued terms of a coordinate reference datum.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `dict`

        '''        
        return ref.datum.parameters()
    #--- End: def

    @staticmethod
    def get_dimension_coordinates(field):
        '''
        '''
        return field.dimension_coordinates()
    #--- End: def

    @staticmethod
    def get_external(parent):
        '''Return whether a construct is external.

:Examples 1:

:Parameters:

    parent: 
        The object

    default: optional

:Returns:

    out: `bool`
        Whether the construct is external.

:Examples 2:
        '''
        return parent.get_external()
    #--- End: def

    @staticmethod
    def get_field_ancillaries(field):
        '''Return the field ancillaries of a field.

:Examples 1:

>>> field_ancillaries = w.get_field_ancillaries(f)

:Parameters:

    field: 
        The field object.

:Returns:

    out: `dict`
        The field ancillary objects, keyed by their internal identifiers.

:Examples 2:

>>> w.get_field_ancillaries(f)
{'fieldancillary0': <FieldAncillary: >,
 'fieldancillary1': <FieldAncillary: >}
        '''
        return field.field_ancillaries()
    #--- End: def

    @staticmethod
    def get_measure(cell_measure):
        '''Return the measure property of a cell measure contruct.

:Examples 1:

>>> measure = w.get_measure(c)

:Parameters:

    cell_measure:
        The cell measure object.

:Returns:

    out: `str` or `None`
        The measure property, or `None` if it has not been set.

:Examples 2:

>>> c
<CellMeasure: area(73, 96) km2>
>>> w.get_measure(c)
'area'
        '''
        return cell_measure.get_measure(None)
    #--- End: def

    @staticmethod
    def get_ncvar(parent, *default):
        '''Return the netCDF variable name.

:Examples 1:

>>> ncvar = w.get_ncvar(x)

:Parameters:

    parent: 
        The object containing the data array.

    default: `str`, optional

:Returns:

    out: 
        The netCDF variable name.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_ncvar(d)
'lat'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_ncvar(b)
'lat_bnds'

>>> w.get_ncvar(x)
AttributeError: Can't get non-existent 'ncvar'
>>> w.get_ncvar(x, 'newname')
'newname'
        '''
        return parent.get_ncvar(*default)
    #--- End: def

    @staticmethod
    def get_ncdim(field, axis, *default):
        '''Return the netCDF variable name.

:Examples 1:

>>> ncdim = w.get_ncdim(x)

:Parameters:

    parent: 
        The object containing the data array.

    default: `str`, optional

:Returns:

    out: 
        The netCDF dimension name.

:Examples 2:
        '''
        return field.get_domain_axis()[axis].get_ncdim(*default)
    #--- End: def

    @staticmethod
    def get_data_ndim(parent):
        '''Return the number of dimensions spanned by the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: int
        The number of dimensions spanned by the data array.

:Examples 1:

>>> ndim = w.get_data_ndim(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_data_ndim(d)
1

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data_ndim(b)
2
        '''
        return parent.data.ndim
    #--- End: def

    @staticmethod
    def get_properties(parent):
        '''Return all properties.

:Parameters:

    parent: 
        The object containing the properties.

:Returns:

    out: `dict`
        The property names and their values

:Examples 1:

>>> properties = w.get_properties(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_properties(d)
{'units: 'degrees_north'}
 'standard_name: 'latitude',
 'foo': 'bar'}
        '''
        return parent.properties()
    #--- End: def

    @staticmethod
    def get_property(parent, prop, *default):
        '''Return a property value.

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: 
        The value of the property.

:Examples 1:

>>> value = w.get_property(x, 'standard_name')

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_property(d, 'units')
'degees_north'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_property(b, 'long_name')
'Latitude Bounds'

>>> w.get_property(x, 'foo')
AttributeError: Can't get non-existent property 'foo'
>>> w.get_property(x, 'foo', 'bar')
'bar'
        '''
        return parent.get_property(prop, *default)
    #--- End: def
    
#    @staticmethod
#    def get_data_shape(parent):
#        '''Return the shape of the data array.
#
#:Parameters:
#
#    parent: 
#        The object containing the data array.
#
#:Returns:
#
#    out: tuple
#        The shape of the data array.
#
#:Examples 1:
#
#>>> shape = w.get_data_shape(x)
#
#:Examples 2:
#
#>>> d
#<DimensionCoordinate: latitude(180) degrees_north>
#>>> w.get_data_shape(d)
#(180,)
#
#>>> b
#<Bounds: latitude(180, 2) degrees_north>
#>>> w.get_data_shape(b)
#(180, 2)
#
#        '''
#        return parent.data.shape
#    #--- End: def

    @staticmethod
    def has_datum(coordinate_reference):
        '''Return True if a coordinate reference has a datum.

:Parameters:

    coordinate_reference: coordinate reference construct

:Returns:

    out: `bool`

:Examples:

>>> if API.has_datum(ref):
...     print ref, 'has a datum'
... else:
...     print ref, 'does not have a datum'

        '''
        return bool(coordinate_reference.datum)
    #--- End: def
    
    @staticmethod
    def has_property(parent, prop):
        '''Return True if a property exists.

:Examples 1:

>>> has_standard_name = w.has_property(x, 'standard_name')

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: `bool`
        `True` if the property exists, otherwise `False`.

:Examples 2:

>>> coord
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.has_property(coord, 'units')
True

>>> bounds
<Bounds: latitude(180, 2) degrees_north>
>>> w.has_property(bounds, 'long_name')
False
        '''
        return parent.has_property(prop)
    #--- End: def
    
    @staticmethod
    def initialise_CoordinateReference(klass, coordinates=None, datum=None,
                                       coordinate_conversion=None, **kwargs):
        '''
        '''
        return klass(coordinates=coordinates,
                     datum=datum, coordinate_conversion=coordinate_conversion)
    #--- End: def

    @staticmethod
    def initialise_Data(klass, data=None, units=None, calendar=None,
                        copy=True):
        '''
        '''
        return klass(data=data, units=units, calendar=calendar,
                     copy=copy)
    #--- End: def

    @staticmethod
    def is_climatology(coordinate):
        '''

:Returns:

    out: `bool`
        The value of the 'climatology' cell extent parameter, or False
        if not set.

        '''
        return bool(coordinate.get_geometry_type(None) == 'climatology')
    #--- End: def

    @staticmethod
    def set_cell_method_axes(cell_method, axes):
        '''
'''
        cell_method.set_axes(axes)
    #--- End: for
    
    @staticmethod
    def set_property(construct, name, value):
        '''
        '''
        construct.set_property(name, value)
    #--- End: def

    @staticmethod
    def set_coordinate_reference_coordinate(coordinate_reference,
                                            coordinate):
        '''
        '''
        coordinate_reference.set_coordinate(coordinate)
    #--- End: def

    @staticmethod
    def squeeze(construct, axes=None, copy=True):
        '''
        '''
        return construct.squeeze(axes=axes, copy=copy)
    #--- End: def
        
#--- End: class
