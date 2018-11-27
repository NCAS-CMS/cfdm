from builtins import super

from .abstract import Implementation


class CFDMImplementation(Implementation):
    '''
    '''
    def __init__(self, cf_version=None,
                 
                 AuxiliaryCoordinate=None,
                 CellMeasure=None,
                 CellMethod=None,
                 CoordinateReference=None,
                 DimensionCoordinate=None,
                 DomainAncillary=None,
                 DomainAxis=None,
                 Field=None,
                 FieldAncillary=None,
                 
                 Bounds=None,
                 List=None,
                 Count=None,
                 Index=None,

                 CoordinateConversion=None,
                 Datum=None,
                 
                 Data=None,
                 GatheredArray=None,
                 NetCDFArray=None,
                 RaggedContiguousArray=None,
                 RaggedIndexedArray=None,
                 RaggedIndexedContiguousArray=None,
    ):
        '''**Initialisation**

:Parameters:

    AuxiliaryCoordinate:
        An auxiliary coordinate construct class.

    CellMeasure:
        A cell measure construct class.

    CellMethod:
        A cell method construct class.

    CoordinateReference:
        A coordinate reference construct class.

    DimensionCoordinate:
        A dimension coordinate construct class.

    DomainAncillary:
        A domain ancillary construct class.

    DomainAxis:
        A domain axis construct class.

    Field:
        A field construct class.

    FieldAncillary:
        A field ancillary construct class.

    Bounds:              = Bounds
    CoordinateAncillary = CoordinateAncillary
    Data                = Data
    NetCDF              = NetCDF

        '''
        super().__init__(
            cf_version=cf_version,

            AuxiliaryCoordinate=AuxiliaryCoordinate,
            CellMeasure=CellMeasure,
            CellMethod=CellMethod,
            CoordinateReference=CoordinateReference,
            DimensionCoordinate=DimensionCoordinate,
            DomainAncillary=DomainAncillary,
            DomainAxis=DomainAxis,
            Field=Field,
            FieldAncillary=FieldAncillary,

            Bounds=Bounds,
            List=List,
            Count=Count,
            Index=Index,
            
            CoordinateConversion=CoordinateConversion,
            Datum=Datum,

            Data=Data,
            GatheredArray=GatheredArray,
            NetCDFArray=NetCDFArray,
            RaggedContiguousArray=RaggedContiguousArray,
            RaggedIndexedArray=RaggedIndexedArray,
            RaggedIndexedContiguousArray=RaggedIndexedContiguousArray,
        )
    #--- End: def

    def construct_expand_dims(self, construct, position):
        '''

:Parameters:

    construct: construct

    position: `int`

    copy: `bool`, optional

:Returns:

    out: construct

        '''
        return construct.expand_dims(position=position)
    #--- End: def

    def copy_construct(self, construct):
        '''
:Returns:

    out:
        The deep copy.
        '''
        return construct.copy()
    #--- End: def

    def create_field(self, field=None, construct_id=None):
        '''TODO
        '''
        return field.create_field(cid=construct_id, domain=False)
    #--- End: def
        
    def del_property(self, construct, prop, default):
        '''

:Parameters:

:Returns:

    out:
        The value of the deleted property

:Examples:

>>> c.set_properties(f, {'standard_name', 'air_temperature'})
>>> c.del_property(f, 'standard_name')
'air_temperature'
>>> c.get_property(f, 'standard_name')
AttributeError: Field doesn't have property 'standard_name'
        
        '''
        return construct.del_property(prop, default)
    #--- End: def

    def field_expand_dims(self, field, position=0, axis=None):
        '''
        '''
        return field.expand_dims(position=position, axis=axis)
    #--- End: def

    def get_array(self, data):
        '''
:Parameters:

    data: `Data`

        '''
        return data.get_array()
    #--- End: def

    def get_auxiliary_coordinates(self, field):
        '''
        '''
        return field.auxiliary_coordinates()
    #--- End: def

    def get_bounds(self, parent, *default):
        '''
        '''
        return parent.get_bounds(*default)
    #--- End: def
    
    def get_cell_measures(self, field):
       '''
       '''
       return field.cell_measures()
    #--- End: def

    def get_cell_methods(self, field):
        '''
        '''
        return field.cell_methods()
    #--- End: def
       
    def get_cell_method_axes(self, cell_method, *default):
        '''

:Returns:

    out: `tuple`
'''
        return cell_method.get_axes(*default)
    #--- End: for
    
    def get_cell_method_string(self, cell_method):
        '''
:Returns:

    out: `str`
'''
        return str(cell_method)
    #--- End: for

    def get_compressed_array(self, data):
        '''

:Parameters:

    data: `Data`

:Returns:

    out: `numpy.ndarray`
        '''
        return data.get_compressed_array()
    #--- End: def

    def get_compressed_axes(self, field, key=None, construct=None):
        '''
:Returns:

    out: `list`
        '''
        if construct is not None:
            data = self.get_data(construct)
        else:
            data = self.get_data(field)
            
        if key is not None:
            data_axes = self.get_construct_axes(field, key)
        else:
            data_axes = self.get_field_data_axes(field)
            
        return [data_axes[i] for i in self.get_data_compressed_axes(data)]
    #--- End: def

    def get_compression_type(self, construct):
        '''
        '''
        return construct.get_data().get_compression_type()
    #--- End: def
        
    def get_construct_axes(self, field, key):
        '''
        '''
        return field.construct_axes(key)
    #--- End: def
    
    def get_constructs(self, field, axes=None):
        '''Return constructs that span particular axes.

If no axes are specified then all constructs are returned.

If axes are specified then constructs whose data arrays span those
axes, and possibly other axes, are returned.

        '''
        return field.constructs(axes=axes)
    #--- End: def
    
    def get_coordinate_reference_coordinates(self, coordinate_reference):
        '''Return the coordinates of a coordinate reference object.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `set`

        '''
        return coordinate_reference.coordinates()
    #--- End: def
    
    def get_coordinate_conversion_parameters(self, coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.coordinate_conversion.parameters()
    #--- End: def

    def get_coordinate_references(self, field):
        '''
        '''
        return field.coordinate_references()
    #--- End: def

    def get_coordinates(self, field):
       '''
:Parameters:

       '''
       return field.coordinates()
    #--- End: def
    
    def get_data_calendar(self, data, *default):
        '''
        '''
        return data.get_calendar(*default)
    #--- End: def

    def get_data_compressed_axes(self, data):
        '''
:Returns:

    out: `list`
        '''
        return data.get_compressed_axes()
    #--- End: def

    def get_data_ndim(self, parent):
        '''Return the number of dimensions spanned by the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: `int`
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

    def get_data_size(self, parent):
        '''Return the number of elements in the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: `int`
        The number of elements in the data array.

:Examples 1:

>>> size = w.get_data_size(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_data_ndim(d)
180

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data_ndim(b)
360
        '''
        return parent.data.size
    #--- End: def

    def get_data_units(self, data, *default):
        '''
        '''
        return data.get_units(*default)
    #--- End: def

    def get_datum(self, coordinate_reference):
        '''
        
:Parameters:

:Returns:

    out: datum object
        
        '''
        return coordinate_reference.datum
    #--- End: def
            
    def get_datum_parameters(self, ref):
        '''Return the parameter-valued terms of a coordinate reference datum.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `dict`

        '''        
        return ref.datum.parameters()
    #--- End: def

    def get_dimension_coordinates(self, field):
        '''
        '''
        return field.dimension_coordinates()
    #--- End: def

    def get_domain_ancillaries(self, field):
       '''
:Parameters:

       '''
       return field.domain_ancillaries()
    #--- End: def

    def get_domain_axes(self, field):
        '''
        '''
        return field.domain_axes()
    #--- End: def
 
    def get_domain_axis_size(self, field, axis):
        '''
        '''
        return field.domain_axes()[axis].get_size()
    #--- End: def

    def get_sample_dimension_position(self, construct):
        '''
        '''
        return construct.get_data().get_compressed_dimension()
    #--- End: def

    def nc_get_instance_dimension(self, index, *default):
        '''TODO
        '''
        return index.nc_get_instance_dimension(*default)
    #--- End: def
    
    def nc_get_sample_dimension(self, count, *default):
        '''TODO
        '''
        return count.nc_get_sample_dimension(*default)
    #--- End: def

    def nc_get_unlimited_axes(self, field):
        '''TODO
        '''
        return field.nc_unlimited_dimensions()
    #--- End: def
    
    def nc_get_global_attributes(self, field):
        '''TODO
        '''
        return field.nc_global_attributes()
    #--- End: def
    
    def nc_set_global_attributes(self, field, attributes):
        '''TODO
        '''
        return field.nc_global_attributes(attributes)
    #--- End: def
    
    def equal_constructs(self, construct0, construct1,
                         ignore_type=False):
        '''

        '''    
        return construct0.equals(construct1, ignore_type=ignore_type)
    #--- End: def

    def equal_properties(self, property_value0, property_value1):
        '''

        '''
        field = self.get_class('Field')()
        return field._equals(property_value0, property_value1)
    #--- End: def

    def equal_datums(self, coordinate_reference0, coordinate_reference1):
        ''':Parameters:

    coordinate_reference0: coordinate reference construct

    coordinate_reference1: coordinate reference construct

:Returns:

    out: `bool`

        '''
        datum0 = coordinate_reference0.datum
        datum1 = coordinate_reference1.datum
        return datum0.equals(datum1)
    #--- End: def

    def get_construct_data_size(self, construct):
        '''

:Parameters:

:Returns:

    out: `int`

        '''
        return construct.data.size
    #--- End: def
   
    def nc_get_external(self, parent):
        '''Return whether a construct is external.

:Parameters:

    parent: 
        The object

:Returns:

    out: `bool`
        Whether the construct is external.

:Examples 2:
        '''
        if not hasattr(parent, 'nc_external'):
            return False
        
        return parent.nc_external()
    #--- End: def
    
    def get_field_ancillaries(self, field):
        '''Return the field ancillaries of a field.

:Examples 1:

>>> x = i.get_field_ancillaries(f)

:Parameters:

    field: 
        The field object.

:Returns:

    out: `dict`
        A dictionary whose values are field ancillary objects, keyed
        by unique identifiers.

:Examples 2:

>>> w.get_field_ancillaries(f)
{'fieldancillary0': <FieldAncillary: ....>,
 'fieldancillary1': <FieldAncillary: ....>}

        '''
        return field.field_ancillaries()
    #--- End: def
                  
    def get_field_data_axes(self, field):
        '''
        '''
        return field.get_data_axes()
    #--- End: def
         
    def get_data_max(self, parent):
        '''

:Parameters:

:Returns:

    out: `int`
        
        '''
        return parent.data.max()
    #--- End: def
    
    def get_data_sum(self, parent):
        '''

:Parameters:

:Returns:

    out: `int`
        
        '''
        return parent.data.sum()
    #--- End: def
    
    def get_count_variable(self, construct):
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
        return construct.get_data().get_count_variable()
    #--- End: def
    
    def get_index_variable(self, construct):
        '''

:Parameters:

  
:Returns:

    out: 

:Examples:

        '''
        return construct.get_data().get_index_variable()
    #--- End: def
    
    def get_list_variable(self, construct):
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
        return construct.get_data().get_list_variable()
    #--- End: def
    
    def get_measure(self, cell_measure):
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
    
    def nc_get_dimension(self, parent, *default):
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
        return parent.nc_get_dimension(*default)
    #--- End: def

    def get_ncvar(self, construct, *default):
       '''

:Parameters:

:Returns:

    out: `str`
       '''
       return construct.nc_get_variable(*default)
    #--- End: def

    def get_properties(self, parent):
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

    def get_property(self, construct, prop, *default):
       '''

:Parameters:

:Returns:

    out:
       '''
       return construct.get_property(prop, *default)
    #--- End: def

    def get_data(self, parent, *default):
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
<Data(180): [-89.5, ..., 89.5] degrees_north>

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data(b)
<Data(180, 2): [[-90, ..., 90]] degrees_north>
        '''
        return parent.get_data(*default)
    #--- End: def

    def initialise_AuxiliaryCoordinate(self):
        '''
        '''
        cls = self.get_class('AuxiliaryCoordinate')
        return cls()
    #--- End: def

    def initialise_Bounds(self):
        '''
        '''
        cls = self.get_class('Bounds')
        return cls()
    #--- End: def

    def initialise_CellMeasure(self, measure=None):
        '''
        '''
        cls = self.get_class('CellMeasure')
        return cls(measure=measure)
    #--- End: def

    def initialise_CellMethod(self, axes=None, properties=None):
        '''
        '''
        cls = self.get_class('CellMethod')
        return cls(axes=axes, properties=properties)
    #--- End: def

    def initialise_CoordinateConversion(self, 
                                        domain_ancillaries=None,
                                        parameters=None):
        '''
        '''
        cls = self.get_class('CoordinateConversion')
        return cls(domain_ancillaries=domain_ancillaries,
                   parameters=parameters)
    #--- End: def

    def initialise_CoordinateReference(self):
        '''
        '''
        cls = self.get_class('CoordinateReference')
        return cls()
    #--- End: def
 
    def initialise_Count(self):
        '''

        '''
        cls = self.get_class('Count')
        return cls()
    #--- End: def

    def initialise_Data(self, array=None, units=None, calendar=None,
                        copy=True):
        '''
:Patameters:

    data:

    units:

    calendar:
        '''
        cls = self.get_class('Data')
        return cls(array=array, units=units, calendar=calendar,
                   copy=copy)
    #--- End: def

    def initialise_Datum(self, parameters=None):
        '''
        '''
        cls = self.get_class('Datum')
        return cls(parameters=parameters)
    #--- End: def

    def initialise_DimensionCoordinate(self, properties=None,
                                       data=None, bounds=None,
                                       interior_ring=None, copy=True):
        '''
        '''
        cls = self.get_class('DimensionCoordinate')
        return cls(properties=properties, data=data, bounds=bounds,
                   interior_ring=interior_ring, copy=copy)
    #--- End: def

    def initialise_DimensionCoordinate_from_AuxiliaryCoordinate(
            self,             auxiliary_coordinate=None,
            copy=True):
        '''
        '''
        cls = self.get_class('DimensionCoordinate')
        return cls(source=auxiliary_coordinate, copy=copy)
    #--- End: def

    def initialise_DomainAncillary(self):
        '''
        '''
        cls = self.get_class('DomainAncillary')
        return cls()
    #--- End: def

    def initialise_DomainAxis(self, size=None):
        '''
        '''
        cls = self.get_class('DomainAxis')
        return cls(size=size)
    #--- End: def

    def initialise_Field(self):
        '''
        '''
        cls = self.get_class('Field')
        return cls()
    #--- End: def

    def initialise_FieldAncillary(self):
        '''
        '''
        cls = self.get_class('FieldAncillary')
        return cls()
    #--- End: def

    def initialise_GatheredArray(self, compressed_array=None,
                                 ndim=None, shape=None, size=None,
                                 compressed_dimension=None,
                                 list_variable=None):
        '''

        '''
        cls = self.get_class('GatheredArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   compressed_dimension=compressed_dimension,
                   list_variable=list_variable)
    #--- End: def

    def initialise_Index(self):
        '''

        '''
        cls = self.get_class('Index')
        return cls()
    #--- End: def

    def initialise_List(self):
        '''

        '''
        cls = self.get_class('List')
        return cls()
    #--- End: def

    def initialise_NetCDFArray(self, filename=None, ncvar=None,
                               dtype=None, ndim=None, shape=None,
                               size=None):
        '''
        '''
        cls = self.get_class('NetCDFArray')
        return cls(filename=filename, ncvar=ncvar, dtype=dtype,
                   ndim=ndim, shape=shape, size=size)
    #--- End: def

    def initialise_RaggedContiguousArray(self, compressed_array=None,
                                         ndim=None, shape=None,
                                         size=None,
                                         count_variable=None):
        '''
        '''
        cls = self.get_class('RaggedContiguousArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   count_variable=count_variable)
    #--- End: def

    def initialise_RaggedIndexedArray(self, compressed_array=None,
                                      ndim=None, shape=None,
                                      size=None, index_variable=None):
        '''
        '''
        cls = self.get_class('RaggedIndexedArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   index_variable=index_variable)
    #--- End: def

    def initialise_RaggedIndexedContiguousArray(self,
                                                compressed_array=None,
                                                ndim=None, shape=None,
                                                size=None,
                                                count_variable=None,
                                                index_variable=None):
        '''
        '''
        cls = self.get_class('RaggedIndexedContiguousArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   count_variable=count_variable,
                   index_variable=index_variable)
    #--- End: def

    def is_climatology(self, coordinate):
        '''

:Returns:

    out: `bool`
        The value of the 'climatology' cell extent parameter, or False
        if not set.

        '''
        return bool(coordinate.get_geometry(None) == 'climatology')
    #--- End: def

    def nc_set_instance_dimension(self, variable, ncdim):
        '''
        '''
        variable.nc_set_instance_dimension(ncdim)
    #--- End: def
    

    def nc_set_sample_dimension(self, variable, ncdim):
        '''
        '''
        variable.nc_set_sample_dimension(ncdim)
    #--- End: def
    
    def set_auxiliary_coordinate(self, field, construct, axes, copy=True):
        '''Insert a auxiliary coordinate object into a field.
        
:Parameters:

    field: `Field`

    construct: `AuxiliaryCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, axes=axes, copy=copy)
    #--- End: def

    def set_bounds(self, construct, bounds, copy=True):
        '''
:Parameters:

:Returns:

    `None`

        '''
        construct.set_bounds(bounds, copy=copy)
    #--- End: def

    def set_cell_measure(self, field, construct, axes, copy=True):
        '''Insert a cell_measure object into a field.

:Parameters:

    field: `Field`

    construct: `CellMeasure`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, axes=axes, copy=copy)
    #--- End: def

    def set_cell_method(self, field, construct, copy=True):
        '''Insert a cell_method object into a field.

:Parameters:

    field: `Field`

    construct: `CellMethod`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
#        return field.set_cell_method(construct, copy=copy)
        return field.set_construct(construct, copy=copy)
    #--- End: def

    def set_cell_method(self, field, construct, copy=True):
        '''Insert a cell_method object into a field.

:Parameters:

    field: `Field`

    construct: `CellMethod`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
#        return field.set_cell_method(construct, copy=copy)
        return field.set_construct(construct, copy=copy)
    #--- End: def

    def set_cell_method_axes(self, cell_method, axes):
        '''
'''
        cell_method.set_axes(axes)
    #--- End: for
    
    def set_coordinate_conversion(self, coordinate_reference, coordinate_conversion):
        '''

:Parameters:

:Returns:

    `None`

        '''
        coordinate_reference.set_coordinate_conversion(coordinate_conversion)
    #--- End: def

    def set_coordinate_reference(self, field, construct, copy=True):
        '''Insert a coordinate reference object into a field.

:Parameters:
    field: `Field`
    construct: `CoordinateReference`
    copy: `bool`, optional
:Returns:
    out: `str`
        '''
        return field.set_construct(construct, copy=copy)
    #--- End: def

    def set_coordinate_reference_coordinates(self,
                                             coordinate_reference,
                                             coordinates):
        '''

:Parameters:

:Returns:

    `None`
        '''
        coordinate_reference.coordinates(coordinates)
    #--- End: def

    def set_coordinate_reference_coordinate(self,
                                            coordinate_reference,
                                            coordinate):
        '''
        '''
        coordinate_reference.set_coordinate(coordinate)
    #--- End: def

    def set_data(self, construct, data, axes=None, copy=True):
        '''

If the construct is a Field then the corresponding domain axes must
also be provided.

:Parameters:

    construct: construct

    data: `Data`

    axes: `tuple`, optional

    copy: `bool`, optional

:Returns:

    `None`
        '''
        if axes is None:
            construct.set_data(data, copy=copy)
        else:
            construct.set_data(data, axes, copy=copy)
    #--- End: def

    def set_datum(self, coordinate_reference, datum):
        '''

:Parameters:

:Returns:

    `None`

        '''
        coordinate_reference.set_datum(datum)
    #--- End: def

    def set_dimension_coordinate(self, field, construct, axes, copy=True):
        '''Insert a dimension coordinate object into a field.
        
:Parameters:

    field: `Field`

    construct: `DimensionCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, axes=axes, copy=copy)
    #--- End: def

    def set_domain_ancillary(self, field, construct, axes, copy=True):
#                             extra_axes=0, copy=True):
        '''Insert a domain ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `DomainAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, axes=axes, copy=copy)
    #--- End: def

    def set_domain_axis(self, field, construct, copy=True):
        '''Insert a domain_axis object into a field.

:Parameters:

    field: `Field`

    construct: `domain_axis`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, copy=copy)
    #--- End: def

    def nc_set_external(self, construct):
        '''
        '''
        construct.nc_external(True)
    #--- End: def

    def set_field_ancillary(self, field, construct, axes, copy=True):
        '''Insert a field ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `FieldAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_construct(construct, axes=axes, copy=copy)
    #--- End: def

    def set_geometry(self, coordinate, value):
        '''
        '''
        coordinate.set_geometry(value)
    #--- End: def

    def set_interior_ring(self, parent, interior_ring, copy=True):
        '''Insert an interior ring array into a coordiante.

:Parameters:

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return parent.set_interior_ring(interior_ring, copy=copy)
    #--- End: def

    def set_read_report(self, field, report):
        '''TODO

..versionadded:: 1.7

        '''
        field._set_read_report(report)
    #-- End: def
    
    def nc_set_dimension(self, construct, ncdim):
        '''
:Parameters:

:Returns:

    `None`

        '''
        construct.nc_set_dimension(ncdim)
    #--- End: def

    def nc_set_variable(self, parent, ncvar):
        '''

:Parameters:

:Returns:

    `None`
        '''
        parent.nc_set_variable(ncvar)
    #--- End: def

    def set_node_ncdim(self, parent, ncdim):
        '''Set the netCDF name of the dimension of a node coordinate variable.

:Parameters:

:Returns:

    `None`

        '''
        parent.set_node_ncdim(ncdim)
    #--- End: def

    def set_part_ncdim(self, parent, ncdim):
        '''Set the netCDF name of the dimension of the part_node_count
variable.

:Parameters:

:Returns:

    `None`

        '''
        parent.set_part_ncdim(ncdim)
    #--- End: def

    def set_properties(self, construct, properties, copy=True):
        '''
:Parameters:

:Returns:

    `None`
        '''
        construct.properties(properties, copy=copy)
    #--- End: def
 
#    def set_size(self, domain_axis, size):
#        '''
#:Parameters:
#
#:Returns:
#
#    `None`
#        '''
#        domain_axis.set_size(size)
#    #--- End: def
 
    def has_bounds(self, construct):
        '''
:Parameters:

:Returns:

    out: `bool`
        '''
        return construct.has_bounds()
    #--- End: def
    
#    def _transpose_data(self, data, axes=None, copy=True):
#        '''
#        '''
#        data = data.tranpose(axes=axes, copy=copy)
#        return data
#    #--- End: def
    
    def has_datum(self, coordinate_reference):
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
    
    def has_property(self, parent, prop):
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
    
    def squeeze(self, construct, axes=None):
        '''
        '''
        return construct.squeeze(axes=axes)
    #--- End: def
        
#--- End: class

