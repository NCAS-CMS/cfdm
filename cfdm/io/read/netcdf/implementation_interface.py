from builtins import object

class API(object):
    '''
    '''
    @staticmethod
    def copy_construct(construct):
        '''
:Returns:

    out:
        The deep copy.
        '''
        return construct.copy()
    #--- End: def

    @staticmethod
    def del_property(construct, prop):
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
        return construct.del_property(prop)
    #--- End: def

    @staticmethod
    def expand_dims(construct, position, copy=True):
        '''

:Parameters:

    construct: construct

    position: `int`

    copy: `bool`, optional

:Returns:

    out: construct

        '''
        return construct.expand_dims(position=position, copy=copy)
    #--- End: def

    @staticmethod
    def get_auxiliary_coordinate(field):
       '''
       '''
       return field.auxiliary_coordinates()
    #--- End: def

    @staticmethod
    def get_bounds(parent, *default):
       '''
       '''
       return parent.get_bounds(*default)
    #--- End: def

    @staticmethod
    def get_cell_measure(field):
       '''
       '''
       return field.cell_measures()
    #--- End: def

    @staticmethod
    def get_coordinates(field):
       '''
:Parameters:

       '''
       return field.coordinates()
    #--- End: def

    @staticmethod
    def get_data(parent, *default):
       '''
       '''
       return parent.get_data(*default)
    #--- End: def

    @staticmethod
    def get_datum(coordinate_reference):
        '''

:Parameters:

:Returns:

    out: datum object
        
        '''
        return coordinate_reference.datum
    #--- End: def

    @staticmethod
    def get_dimension_coordinate(field):
       '''
:Parameters:

       '''
       return field.dimension_coordinates()
    #--- End: def

    @staticmethod
    def get_domain_ancillary(field):
       '''
:Parameters:

       '''
       return field.domain_ancillaries()
    #--- End: def

    @staticmethod
    def get_field_ancillary(field):
       '''
:Parameters:

       '''
       return field.field_ancillaries()
    #--- End: def
                                  
#    @staticmethod
#    def get_fill_value(construct):
#       '''
#:Parameters:
#
#:Returns:
#
#    out: 
#       The fill value, or `None` if there is no fill value.
#
#       '''
#       try:
#           return construct.fill_value()
#       except AttributeError:
#           return
#    #--- End: def
                                  
    @staticmethod
    def get_int_max(data):
        '''

:Parameters:

:Returns:

    out: `int`
        
        '''
        return int(data.max())
    #--- End: def
    
    @staticmethod
    def get_interior_ring(parent, *default):
       '''
       '''
       return parent.get_interior_ring(*default)
    #--- End: def

    @staticmethod
    def get_ncvar(construct, *default):
       '''

:Parameters:

:Returns:

    out: `str`
       '''
       return construct.get_ncvar(*default)
    #--- End: def

    @staticmethod
    def get_properties(construct):
        '''
:Parameters:

:Returns:

    `None`
        '''
        return construct.properties()
    #--- End: def
 
    @staticmethod
    def get_property(construct, prop, *default):
       '''

:Parameters:

:Returns:

    out:
       '''
       return construct.get_property(prop, *default)
    #--- End: def

    @staticmethod
    def get_size(x):
        '''

:Parameters:

:Returns:

    out: `int`

        '''
        return x.size
    #--- End: def

    @staticmethod
    def set_auxiliary_coordinate(field, construct, axes, copy=True):
        '''Insert a auxiliary coordinate object into a field.
        
:Parameters:

    field: `Field`

    construct: `AuxiliaryCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_auxiliary_coordinate(construct, axes=axes, copy=copy)
    #--- End: def

    @staticmethod
    def set_bounds(construct, bounds, copy=True):
        '''
:Parameters:

:Returns:

    `None`

        '''
        construct.set_bounds(bounds, copy=copy)
    #--- End: def

    @staticmethod
    def set_cell_measure(field, construct, axes, copy=True):
        '''Insert a cell_measure object into a field.

:Parameters:

    field: `Field`

    construct: `CellMeasure`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_cell_measure(construct, axes=axes, copy=copy)
    #--- End: def

    @staticmethod
    def set_cell_method(field, construct, copy=True):
        '''Insert a cell_method object into a field.

:Parameters:

    field: `Field`

    construct: `CellMethod`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_cell_method(construct, copy=copy)
    #--- End: def

    @staticmethod
    def set_coordinate_reference(field, construct, copy=True):
        '''Insert a coordinate reference object into a field.

:Parameters:

    field: `Field`

    construct: `CoordinateReference`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_coordinate_reference(construct, copy=copy)
    #--- End: def

    @staticmethod
    def set_coordinate_reference_coordinates(coordinate_reference,
                                             coordinates):
        '''

:Parameters:

:Returns:

    `None`
        '''
        coordinate_reference.coordinates(coordinates)
    #--- End: def

    @staticmethod
    def set_data(construct, data, axes=None, copy=True):
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

    @staticmethod
    def set_datum(coordinate_reference, datum):
        '''

:Parameters:

:Returns:

    `None`

        '''
        coordinate_reference.set_datum(datum)
    #--- End: def

    @staticmethod
    def set_dimension_coordinate(field, construct, axes, copy=True):
        '''Insert a dimension coordinate object into a field.
        
:Parameters:

    field: `Field`

    construct: `DimensionCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_dimension_coordinate(construct, axes=axes, copy=copy)
    #--- End: def

    @staticmethod
    def set_domain_ancillary(field, construct, axes, extra_axes=0,
                             copy=True):
        '''Insert a domain ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `DomainAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_domain_ancillary(construct, axes=axes,
                                          extra_axes=extra_axes,
                                          copy=copy)
    #--- End: def

    @staticmethod
    def set_domain_axis(field, construct, copy=True):
        '''Insert a domain_axis object into a field.

:Parameters:

    field: `Field`

    construct: `domain_axis`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_domain_axis(construct, copy=copy)
    #--- End: def

    @staticmethod
    def set_external(construct):
        '''
        '''
        construct.set_external(True)
    #--- End: def

    @staticmethod
    def set_field_ancillary(field, construct, axes, copy=True):
        '''Insert a field ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `FieldAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_field_ancillary(construct, axes=axes, copy=copy)
    #--- End: def

    @staticmethod
    def set_geometry_type(coordinate, value):
        '''
        '''
        coordinate.set_geometry_type(value)
    #--- End: def

    @staticmethod
    def set_interior_ring(parent, interior_ring, copy=True):
        '''Insert an interior ring array into a coordiante.

:Parameters:

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return parent.set_interior_ring(interior_ring, copy=copy)
    #--- End: def

    @staticmethod
    def set_ncdim(construct, ncdim):
        '''
:Parameters:

:Returns:

    `None`

        '''
        construct.set_ncdim(ncdim)
    #--- End: def

    @staticmethod
    def set_ncvar(parent, ncvar):
        '''

:Parameters:

:Returns:

    `None`
        '''
        parent.set_ncvar(ncvar)
    #--- End: def

    @staticmethod
    def set_node_ncdim(parent, ncdim):
        '''Set the netCDF name of the dimension of a node coordinate variable.

:Parameters:

:Returns:

    `None`

        '''
        parent.set_node_ncdim(ncdim)
    #--- End: def

    @staticmethod
    def set_part_ncdim(parent, ncdim):
        '''Set the netCDF name of the dimension of the part_node_count
variable.

:Parameters:

:Returns:

    `None`

        '''
        parent.set_part_ncdim(ncdim)
    #--- End: def

    @staticmethod
    def set_properties(construct, properties, copy=True):
        '''
:Parameters:

:Returns:

    `None`
        '''
        construct.properties(properties, copy=copy)
    #--- End: def
 
#    @staticmethod
#    def set_size(domain_axis, size):
#        '''
#:Parameters:
#
#:Returns:
#
#    `None`
#        '''
#        domain_axis.set_size(size)
#    #--- End: def
 
    @staticmethod
    def has_bounds(construct):
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
    
    @staticmethod
    def initialise_AuxiliaryCoordinate(klass, **kwargs):
        '''
        '''
        return klass(**kwargs)
    #--- End: def

    @staticmethod
    def initialise_Bounds(klass, **kwargs):
        '''
        '''
        return klass(**kwargs)
    #--- End: def

    @staticmethod
    def initialise_CellMeasure(klass, measure=None, **kwargs):
        '''
        '''
        return klass(measure=measure, **kwargs)
    #--- End: def

    @staticmethod
    def initialise_CellMethod(klass, axes=None, properties=None, **kwargs):
        '''
        '''
        return klass(axes=axes, properties=properties, **kwargs)
    #--- End: def

    @staticmethod
    def initialise_CompressedArray(klass, array=None,
                                   uncompressed_ndim=None,
                                   uncompressed_shape=None,
                                   uncompressed_size=None,
                                   compression_type=None,
                                   compression_parameters=None):
        '''
        '''
        return klass(array=array,
                     ndim=uncompressed_ndim,
                     shape=uncompressed_shape,
                     size=uncompressed_size,
                     compression_type=compression_type,
                     compression_parameters=compression_parameters)
    #--- End: def

    @staticmethod
    def initialise_CoordinateReference(klass, coordinates=None,
                                       domain_ancillaries=None,
                                       parameters=None, **kwargs):
        '''
        '''
        return klass(coordinates=coordinates,
                     domain_ancillaries=domain_ancillaries,
                     parameters=parameters, **kwargs)
    #--- End: def

    @staticmethod
    def initialise_Data(klass, data=None, units=None, calendar=None,
                        copy=True):
        '''
:Patameters:

    klass: 

    data:

    units:

    calendar:
        '''
        return klass(data=data, units=units, calendar=calendar,
                     copy=copy)
    #--- End: def

    @staticmethod
    def initialise_DimensionCoordinate(klass, properties=None,
                                       data=None, bounds=None,
                                       interior_ring=None, copy=True):
        '''
        '''
        return klass(properties=properties, data=data, bounds=bounds,
                     interior_ring=interior_ring, copy=copy)
    #--- End: def

    @staticmethod
    def initialise_DimensionCoordinate_from_AuxiliaryCoordinate(
            klass,
            auxiliary_coordinate=None,
            copy=True):
        '''
        '''
        return klass(source=auxiliary_coordinate, copy=copy)
    #--- End: def

    @staticmethod
    def initialise_DomainAncillary(klass, **kwargs):
        '''
        '''
        return klass(**kwargs)
    #--- End: def

    @staticmethod
    def initialise_DomainAxis(klass, size=None, **kwargs):
        '''
        '''
        return klass(size=size, **kwargs)
    #--- End: def

    @staticmethod
    def initialise_Field(klass, **kwargs):
        '''
        '''
        return klass(**kwargs)
    #--- End: def

    @staticmethod
    def initialise_FieldAncillary(klass, **kwargs):
        '''
        '''
        return klass(**kwargs)
    #--- End: def

    @staticmethod
    def initialise_GatheredArray(klass, array=None, ndim=None,
                                 shape=None, size=None,
                                 sample_axis=None,
                                 indices=None):
        '''
        '''
        return klass(array=array,
                     ndim=ndim,
                     shape=shape,
                     size=size,
                     sample_axis=sample_axis,
                     indices=indices)
    #--- End: def

    @staticmethod
    def initialise_NetCDFArray(klass, filename=None, ncvar=None,
                               dtype=None, ndim=None, shape=None,
                               size=None, **kwargs):
        '''
        '''
        return klass(filename=filename, ncvar=ncvar, dtype=dtype,
                     ndim=ndim, shape=shape, size=size, **kwargs)
    #--- End: def

    @staticmethod
    def initialise_RaggedContiguousArray(klass, array=None, ndim=None,
                                         shape=None, size=None,
                                         elements_per_instance=None):
        '''
        '''
        return klass(array=array,
                     ndim=ndim,
                     shape=shape,
                     size=size,
                     elements_per_instance=elements_per_instance)
    #--- End: def

    @staticmethod
    def initialise_RaggedIndexedArray(klass, array=None, ndim=None,
                                      shape=None, size=None,
                                      instances=None):
        '''
        '''
        return klass(array=array,
                     ndim=ndim,
                     shape=shape,
                     size=size,
                     instances=instances)
    #--- End: def

    @staticmethod
    def initialise_RaggedIndexedContiguousArray(klass, array=None,
                                                ndim=None, shape=None,
                                                size=None,
                                                profile_indices=None,
                                                elements_per_profile=None):
        '''
        '''
        return klass(array=array,
                     ndim=ndim,
                     shape=shape,
                     size=size,
                     profile_indices=profile_indices,
                     elements_per_profile=elements_per_profile)
    #--- End: def

#--- End: class

