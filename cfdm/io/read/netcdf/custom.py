#import struct


class Custom(object):
    '''
    '''

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
    def get_ncvar(construct, *default):
       '''

:Parameters:

:Returns:

    out: `str`
       '''
       return construct.get_ncvar(*default)
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
        '''
:Parameters:

:Returns:

    `None`
        '''
        parent.set_node_ncdim(ncdim)
    #--- End: def

    @staticmethod
    def set_part_ncdim(parent, ncdim):
        '''
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
 
    @staticmethod
    def set_size(domain_axis, size):
        '''
:Parameters:

:Returns:

    `None`
        '''
        domain_axis.set_size(size)
    #--- End: def
 
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
    
    def initialise(self, object_type, **kwargs):
        '''
        '''
        return self.implementation.get_class(object_type)(**kwargs)
    #--- End: def

    def create_compressed_array(self, array=None,
                                uncompressed_ndim=None,
                                uncompressed_shape=None,
                                uncompressed_size=None,
                                compression_type=None,
                                compression_parameters=None):
        '''
        '''
        return self.initialise('CompressedArray',
            array=array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            compression_type=compression_type,
            compression_parameters=compression_parameters)
    #--- End: def
    
#--- End: class

