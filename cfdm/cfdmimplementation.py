from . import (AuxiliaryCoordinate,
               CellMethod,
               CellMeasure,
               CoordinateReference,
               DimensionCoordinate,
               DomainAncillary,
               DomainAxis,
               Field,
               FieldAncillary,
               Bounds,
               InteriorRing,
               CoordinateConversion,
               Datum,
               Count,
               List,
               Index,
               NodeCountProperties,
               PartNodeCountProperties)

from .data import (Data,
                   GatheredArray,
                   NetCDFArray,
                   RaggedContiguousArray,
                   RaggedIndexedArray,
                   RaggedIndexedContiguousArray)

from .abstract import Implementation

from . import CF


class CFDMImplementation(Implementation):
    '''TODO

    .. versionadded:: 1.7.0

    '''
    def __init__(
            self,

            cf_version=None,

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
            InteriorRing=None,
            CoordinateConversion=None,
            Datum=None,
            Data=None,

            GatheredArray=None,
            NetCDFArray=None,
            RaggedContiguousArray=None,
            RaggedIndexedArray=None,
            RaggedIndexedContiguousArray=None,

            List=None,
            Count=None,
            Index=None,
            NodeCountProperties=None,
            PartNodeCountProperties=None,
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

        Bounds:             = Bounds
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
            InteriorRing=InteriorRing,
            CoordinateConversion=CoordinateConversion,
            Datum=Datum,
            Data=Data,

            GatheredArray=GatheredArray,
            NetCDFArray=NetCDFArray,
            RaggedContiguousArray=RaggedContiguousArray,
            RaggedIndexedArray=RaggedIndexedArray,
            RaggedIndexedContiguousArray=RaggedIndexedContiguousArray,

            List=List,
            Count=Count,
            Index=Index,
            NodeCountProperties=NodeCountProperties,
            PartNodeCountProperties=PartNodeCountProperties,
        )

    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

        '''
        return '<{0}: >'.format(self.__class__.__name__)

    def bounds_insert_dimension(self, bounds, position):
        '''TODO

    :Parameters:

        bounds: `Bounds`

        position: `int`

    :Returns:

        `Bounds`

        '''
        return bounds.insert_dimension(position=position)

    def conform_geometry_variables(self, field):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

        field: Field construct

    :Returns:

        `bool`
            TODO
        '''
        out = {'node_count': {},
               'part_node_count': {},
               'interior_ring': {}}

        for coord in self.get_auxiliary_coordinates(field).values():
            for variable in out:
                x = getattr(self, 'get_'+variable)(coord)
                if x is None:
                    continue

                for k, v in x.properties().items():
                    if k not in out[variable]:
                        out[variable][k] = v
                    elif v != out[variable][k]:
                        return False
        # --- End: for

        for coord in self.get_auxiliary_coordinates(field).values():
            for variable in out:
                x = getattr(self, 'get_'+variable)(coord)
                if x is None:
                    continue

                x.set_properties(out[variable])
        # --- End: for

        return True

    def construct_insert_dimension(self, construct, position):
        '''TODO

    :Parameters:

        construct: construct

        position: `int`

        copy: `bool`, optional

    :Returns:

        construct

        '''
        return construct.insert_dimension(position=position)

    def copy_construct(self, construct):
        '''TODO

    :Returns:

            The deep copy.

        '''
        return construct.copy()

    def convert(self, field=None, construct_id=None):
        '''TODO

        '''
        return field.convert(construct_id, full_domain=False)

#    def data_insert_dimension_inplace(self, data, position):
#        '''TODO
#
#    :Parameters:
#
#        data: `Data`
#
#        position: `int`
#
#    :Returns:
#
#        `None`
#
#        '''
#        data.insert_dimension(position=position, inplace=True)

    def del_property(self, construct, prop, default):
        '''TODO

    :Parameters:

    :Returns:

            The value of the deleted property

    **Examples:**

    >>> c.set_properties(f, {'standard_name', 'air_temperature'})
    >>> c.del_property(f, 'standard_name')
    'air_temperature'
    >>> c.get_property(f, 'standard_name')
    AttributeError: Field doesn't have property 'standard_name'

        '''
        return construct.del_property(prop, default)

    def field_insert_dimension(self, field, position=0, axis=None):
        '''TODO
        '''
        return field.insert_dimension(axis, position=position)

    def get_array(self, data):
        '''TODO

    :Parameters:

        data: `Data`

        '''
        return data.array

    def get_auxiliary_coordinates(self, field, axes=[], exact=False):
        '''Return auxiliary coordinate constructs that span particular axes.

    If no axes are specified then all auxiliary coordinate constructs
    are returned.

    If axes are specified then auxiliary coordinate constructs whose
    data arrays span those axes, and possibly other axes, are
    returned.

    :Parameters:

        axes: sequence of `str`

    :Returns:

        `dict`

        '''
        if exact:
            arg = 'exact'
        else:
            arg = 'and'

        return dict(field.auxiliary_coordinates.filter_by_axis(
            arg, *axes))

    def get_bounds(self, parent, default=None):
        '''TODO
        '''
        return parent.get_bounds(default=default)

    def get_bounds_ncvar(self, parent, default=None):
        '''TODO
        '''
        bounds = parent.get_bounds(None)
        if bounds is None:
            return default

        return self.nc_get_variable(bounds, default=default)

    def get_cell_measures(self, field):
        '''TODO
        '''
        return field.cell_measures

    def get_cell_methods(self, field):
        '''TODO
        '''
        return field.cell_methods.ordered()

    def get_cell_method_axes(self, cell_method, default=None):
        '''TODO

    :Returns:

        `tuple`

        '''
        return cell_method.get_axes(default=default)

    def get_cell_method_string(self, cell_method):
        '''TODO

    :Returns:

        `str`

        '''
        return str(cell_method)

    def get_cell_method_qualifiers(self, cell_method):
        '''TODO

    :Returns:

        `str`

        '''
        return cell_method.qualifiers()

    def get_compressed_array(self, data):
        '''TODO

    :Parameters:

        data: `Data`

    :Returns:

        `numpy.ndarray`

        '''
        return data.compressed_array

    def get_compressed_axes(self, field, key=None, construct=None):
        '''TODO

    :Returns:

        `list`

        '''
        if construct is not None:
            data = self.get_data(construct)
        else:
            data = self.get_data(field)

        if key is not None:
            data_axes = self.get_construct_data_axes(field, key)
        else:
            data_axes = self.get_field_data_axes(field)

        return [data_axes[i] for i in self.get_data_compressed_axes(data)]

    def get_compression_type(self, construct):
        '''TODO

    :Parameters:

        construct:

    :Returns:

        `str`
            The compression type. If there is no compression then an
            empty string is returned.

        '''
        data = construct.get_data(None)
        if data is None:
            return ''

        return data.get_compression_type()

    def get_construct_data_axes(self, field, key):
        '''TODO
        '''
        return field.constructs.data_axes()[key]

    def get_constructs(self, field, axes=[], data=False):
        '''Return constructs that span particular axes.

    If no axes are specified then all constructs are returned.

    If axes are specified then constructs whose data arrays span those
    axes, and possibly other axes, are returned.

    :Parameters:

        axes: sequence of `str`

        data: `bool`
            If True then only return constructs that can contain data.

    :Returns:

        `dict`

        '''
        if data:
            return dict(field.constructs.filter_by_data())

        return dict(field.constructs.filter_by_axis('and', *axes))

    def get_coordinate_reference_coordinates(self, coordinate_reference):
        '''Return the coordinates of a coordinate reference object.

    :Parameters:

        coordinate_reference: `CoordinateReference`

    :Returns:

        `set`

        '''
        return coordinate_reference.coordinates()

    def get_coordinate_conversion_parameters(self, coordinate_reference):
        '''TODO

    :Returns:

        `dict`

        '''
        return coordinate_reference.coordinate_conversion.parameters()

    def get_coordinate_references(self, field):
        '''TODO
        '''
        return field.coordinate_references

    def get_coordinates(self, field):
        '''TODO

    :Parameters:

        '''
        return field.coordinates

    def get_data_calendar(self, data, default=None):
        '''TODO
        '''
        return data.get_calendar(default=default)

    def get_data_compressed_axes(self, data):
        '''TODO

    :Returns:

        `list`

        '''
        return data.get_compressed_axes()

    def get_data_ndim(self, parent):
        '''Return the number of dimensions spanned by the data array.

    :Parameters:

        parent:
            The object containing the data array.

    :Returns:

        `int`
            The number of dimensions spanned by the data array.

    **Examples:**

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

    def get_data_shape(self, parent):
        '''Return the shape of the data array.

    :Parameters:

        parent:
            The object containing the data array.

    :Returns:

        `tuple`
            The shape of the data array.

    **Examples:**

    >>> d
    <DimensionCoordinate: latitude(180) degrees_north>
    >>> w.get_data_shape(d)
    (180,)

    >>> b
    <Bounds: latitude(180, 2) degrees_north>
    >>> w.get_data_shape(b)
    (180, 2)

        '''
        return parent.data.shape

    def get_data_size(self, parent):
        '''Return the number of elements in the data array.

    :Parameters:

        parent:
            The object containing the data array.

    :Returns:

        `int`
            The number of elements in the data array.

    **Examples:**

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

    def get_data_units(self, data, default=None):
        '''TODO

        '''
        return data.get_units(default=default)

    def get_datum(self, coordinate_reference):
        '''TODO

    :Parameters:

    :Returns:

        datum object

        '''
        return coordinate_reference.datum

    def get_datum_parameters(self, ref):
        '''Return the parameter-valued terms of a coordinate reference datum.

    :Parameters:

        coordinate_reference: `CoordinateReference`

    :Returns:

        `dict`

        '''
        return ref.datum.parameters()

    def get_dimension_coordinates(self, field):
        '''TODO
        '''
        return field.dimension_coordinates

    def get_domain_ancillaries(self, field):
        '''TODO

        '''
        return field.domain_ancillaries

    def get_domain_axes(self, field):
        '''TODO

        '''
        return field.domain_axes

    def get_domain_axis_size(self, field, axis):
        '''TODO
        '''
        return field.domain_axes[axis].get_size()

    def get_sample_dimension_position(self, construct):
        '''TODO

        '''
        return construct.get_data().get_compressed_dimension()

    def nc_get_geometry_variable(self, field, default=None):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

    :Returns:

        `str`

        '''
        return field.nc_get_geometry_variable(default)

    def nc_get_hdf5_chunksizes(self, data):
        '''Return the HDF5 chunksizes for the data.

    ..versionadded:: 1.7.2

    :Parameters:

        data: Data instance

    :Returns:

        `tuple` or `None`
            The HDF5 chunksizes, or `None` if they haven't been set.

        '''
        out = data.nc_hdf5_chunksizes()
        if not out:
            out = None

        return out

    def nc_get_sample_dimension(self, count, default=None):
        '''Return the name of the netCDF sample dimension.

    :Returns:

        `str`
            The name of the netCDF sample dimension.

        '''
        return count.nc_get_sample_dimension(default=default)

    def nc_is_unlimited_axis(self, field, axis):
        '''Whether a domain axis corresponds to a netCDF unlimited dimension.

    .. versionadded:: 1.7.0

    :Parameters:

        field: `Field`

    :Returns:

        `set`
            The selection of domain axis construct identifiers that are
            unlimited.

        '''
        domain_axis = field.constructs.get(axis)
        if domain_axis is None:
            return False

        return domain_axis.nc_is_unlimited()

    def nc_set_unlimited_axis(self, field, axis):
        '''Set a domain axis to correspond to a netCDF unlimited dimension.

    .. versionadded:: 1.7.4

    :Parameters:

        field: `Field`

        axis: `str`
            Domain axis construct key.

    :Returns:

        `None`

        '''
        domain_axis = field.constructs.get(axis)
        if domain_axis is None:
            return

        domain_axis.nc_set_unlimited(True)

    def nc_get_global_attributes(self, field):
        '''TODO

        '''
        return field.nc_global_attributes()

    def nc_set_global_attributes(self, field, attributes):
        '''TODO

    .. versionadded:: 1.7.0

    attributes: `dict`

        '''
        for attr, value in attributes.items():
            field.nc_set_global_attribute(attr, value)

    def equal_constructs(self, construct0, construct1,
                         ignore_type=False):
        '''TODO

        '''
        return construct0.equals(construct1, ignore_type=ignore_type)

    def equal_properties(self, property_value0, property_value1):
        '''TODO

        '''
        field = self.get_class('Field')()
        return field._equals(property_value0, property_value1)

    def equal_datums(self, coordinate_reference0, coordinate_reference1):
        '''TODO

    :Parameters:

        coordinate_reference0: coordinate reference construct

        coordinate_reference1: coordinate reference construct

    :Returns:

        `bool`

        '''
        datum0 = coordinate_reference0.datum
        datum1 = coordinate_reference1.datum
        return datum0.equals(datum1)

    def get_construct_data_size(self, construct):
        '''TODO

    :Parameters:

    :Returns:

        `int`

        '''
        return construct.data.size

    def nc_get_external(self, parent):
        '''Return whether a construct is external.

    :Parameters:

        parent:
            The object

    :Returns:

        `bool`
            Whether the construct is external.

        '''
        if not hasattr(parent, 'nc_get_external'):
            return False

        return parent.nc_get_external()

    def get_field_ancillaries(self, field):
        '''Return the field ancillaries of a field.

    :Parameters:

        field:
            The field object.

    :Returns:

        `dict`
            A dictionary whose values are field ancillary objects, keyed
            by unique identifiers.

    **Examples:**

    >>> w.get_field_ancillaries(f)
    {'fieldancillary0': <FieldAncillary: ....>,
     'fieldancillary1': <FieldAncillary: ....>}

        '''
        return field.field_ancillaries

    def get_field_data_axes(self, field):
        '''TODO

    :Returns:

        `tuple`

        '''
        return field.get_data_axes()

    def get_filenames(self, parent):
        '''TODO
'''
        return parent.get_filenames()

    def get_data_max(self, parent):
        '''Use `get_data_maximum` instead (since cfdm version 1.8.0).

        '''
        raise NotImplementedError(
            "Use `get_data_maximum` instead (since cfdm version 1.8.0).")

    def get_data_maximum(self, parent):
        '''TODO

    :Parameters:

    :Returns:

        `int`

        '''
        return parent.data.maximum()

    def get_data_sum(self, parent):
        '''TODO

    :Parameters:

    :Returns:

        `int`

        '''
        return parent.data.sum()

    def get_count(self, construct):
        '''Return the measure property of a cell measure construct.

    :Parameters:

        cell_measure:
            The cell measure object.

    :Returns:

        `str` or `None`
            The measure property, or `None` if it has not been set.

    **Examples:**

    >>> c
    <CellMeasure: area(73, 96) km2>
    >>> w.get_measure(c)
    'area'
        '''
        return construct.get_data().get_count(default=None)

    def get_index(self, construct):
        '''TODO

    :Parameters:


    :Returns:

        '''
        return construct.get_data().get_index(default=None)

    def get_interior_ring(self, construct):
        '''TODO

    :Parameters:

        TODO

    :Returns:

        TODO

        '''
        return construct.get_interior_ring(default=None)

    def get_list(self, construct):
        '''TODO

        '''
        return construct.get_data().get_list(default=None)

    def get_measure(self, cell_measure):
        '''Return the measure property of a cell measure construct.

    :Parameters:

        cell_measure:
            The cell measure object.

    :Returns:

        `str` or `None`
            The measure property, or `None` if it has not been set.

    **Examples:**

    >>> c
    <CellMeasure: area(73, 96) km2>
    >>> w.get_measure(c)
    'area'
        '''
        return cell_measure.get_measure(default=None)

    def nc_get_dimension(self, parent, default=None):
        '''Return the netCDF variable name.

    :Parameters:

        parent:
            The object containing the data array.

        default: `str`, optional

    :Returns:

        `str`
            The netCDF dimension name.

    **Examples:**

        '''
        return parent.nc_get_dimension(default=default)

    def nc_get_variable(self, construct, default=None):
        '''TODO

    :Parameters:

        TODO

    :Returns:

        `str`
           TODO
        '''
        return construct.nc_get_variable(default=default)

    def get_node_count(self, construct):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

        construct:

    :Returns:

        Node count variable

        '''
        return construct.get_node_count(default=None)

    def get_part_node_count(self, construct):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:


    :Returns:

        Part node count variable


        '''
        return construct.get_part_node_count(default=None)

    def get_properties(self, parent):
        '''Return all properties.

    :Parameters:

        parent:
            The object containing the properties.

    :Returns:

        `dict`
            The property names and their values

    **Examples:**

    >>> d
    <DimensionCoordinate: latitude(180) degrees_north>
    >>> w.get_properties(d)
    {'units: 'degrees_north'}
     'standard_name: 'latitude',
     'foo': 'bar'}
        '''
        return parent.properties()

    def get_property(self, construct, prop, default=None):
        '''TODO

    :Parameters:

    :Returns:

        '''
        return construct.get_property(prop, default=default)

    def get_geometry(self, construct, default=None):
        '''TODO

    :Parameters:

    :Returns:

        '''
        return construct.get_geometry(default=default)

    def get_data(self, parent, default=None):
        '''Return the data array.

    :Parameters:

        parent:
            The object containing the data array.

    :Returns:

            The data.

    **Examples:**

    >>> d
    <DimensionCoordinate: latitude(180) degrees_north>
    >>> w.get_data(d)
    <Data(180): [-89.5, ..., 89.5] degrees_north>

    >>> b
    <Bounds: latitude(180, 2) degrees_north>
    >>> w.get_data(b)
    <Data(180, 2): [[-90, ..., 90]] degrees_north>
        '''
        return parent.get_data(default=default)

    def initialise_AuxiliaryCoordinate(self):
        '''TODO
        '''
        cls = self.get_class('AuxiliaryCoordinate')
        return cls()

    def initialise_Bounds(self):
        '''TODO
        '''
        cls = self.get_class('Bounds')
        return cls()

    def initialise_CellMeasure(self, measure=None):
        '''TODO
        '''
        cls = self.get_class('CellMeasure')
        return cls(measure=measure)

    def initialise_CellMethod(self, axes=None, method=None,
                              qualifiers=None):
        '''TODO
        '''
        cls = self.get_class('CellMethod')
        return cls(axes=axes, method=method, qualifiers=qualifiers)

    def initialise_CoordinateConversion(self,
                                        domain_ancillaries=None,
                                        parameters=None):
        '''TODO
        '''
        cls = self.get_class('CoordinateConversion')
        return cls(domain_ancillaries=domain_ancillaries,
                   parameters=parameters)

    def initialise_CoordinateReference(self):
        '''TODO
        '''
        cls = self.get_class('CoordinateReference')
        return cls()

    def initialise_Count(self):
        '''TODO

        '''
        cls = self.get_class('Count')
        return cls()

    def initialise_Data(self, array=None, units=None, calendar=None,
                        copy=True, **kwargs):
        '''TODO

    :Patameters:

        array:

        units:

        calendar:

        copy: `bool`, optional

        kwargs: optional
            Not used in this imlementation

    :Returns;

        `Data`
            TODO

        '''
        cls = self.get_class('Data')
        return cls(array=array, units=units, calendar=calendar,
                   copy=copy, **kwargs)

    def initialise_Datum(self, parameters=None):
        '''TODO
        '''
        cls = self.get_class('Datum')
        return cls(parameters=parameters)

    def initialise_DimensionCoordinate(self, properties=None,
                                       data=None, bounds=None,
                                       interior_ring=None, copy=True):
        '''TODO
        '''
        cls = self.get_class('DimensionCoordinate')
        return cls(properties=properties, data=data, bounds=bounds,
                   interior_ring=interior_ring, copy=copy)

    def initialise_DimensionCoordinate_from_AuxiliaryCoordinate(
            self,
            auxiliary_coordinate=None,
            copy=True):
        '''TODO
        '''
        cls = self.get_class('DimensionCoordinate')
        return cls(source=auxiliary_coordinate, copy=copy)

    def initialise_DomainAncillary(self):
        '''TODO
        '''
        cls = self.get_class('DomainAncillary')
        return cls()

    def initialise_DomainAxis(self, size=None):
        '''TODO
        '''
        cls = self.get_class('DomainAxis')
        return cls(size=size)

    def initialise_Field(self):
        '''TODO
        '''
        cls = self.get_class('Field')
        return cls()

    def initialise_FieldAncillary(self):
        '''TODO
        '''
        cls = self.get_class('FieldAncillary')
        return cls()

    def initialise_GatheredArray(self, compressed_array=None,
                                 ndim=None, shape=None, size=None,
                                 compressed_dimension=None,
                                 list_variable=None):
        '''TODO

        '''
        cls = self.get_class('GatheredArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   compressed_dimension=compressed_dimension,
                   list_variable=list_variable)

    def initialise_Index(self):
        '''TODO

        '''
        cls = self.get_class('Index')
        return cls()

    def initialise_InteriorRing(self):
        '''TODO

        '''
        cls = self.get_class('InteriorRing')
        return cls()

    def initialise_List(self):
        '''TODO

        '''
        cls = self.get_class('List')
        return cls()

    def initialise_NetCDFArray(self, filename=None, ncvar=None,
                               dtype=None, ndim=None, shape=None,
                               size=None, mask=True):
        '''TODO

    :Returns:

        `NetCDFArray`

        '''
        cls = self.get_class('NetCDFArray')
        return cls(filename=filename, ncvar=ncvar, dtype=dtype,
                   ndim=ndim, shape=shape, size=size, mask=mask)

    def initialise_NodeCount(self):
        '''

        '''
        cls = self.get_class('NodeCountProperties')
        return cls()

    def initialise_PartNodeCount(self):
        '''TODO

        '''
        cls = self.get_class('PartNodeCountProperties')
        return cls()

    def initialise_RaggedContiguousArray(self, compressed_array=None,
                                         ndim=None, shape=None,
                                         size=None,
                                         count_variable=None):
        '''TODO
        '''
        cls = self.get_class('RaggedContiguousArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   count_variable=count_variable)

    def initialise_RaggedIndexedArray(self, compressed_array=None,
                                      ndim=None, shape=None,
                                      size=None, index_variable=None):
        '''TODO
        '''
        cls = self.get_class('RaggedIndexedArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   index_variable=index_variable)

    def initialise_RaggedIndexedContiguousArray(self,
                                                compressed_array=None,
                                                ndim=None, shape=None,
                                                size=None,
                                                count_variable=None,
                                                index_variable=None):
        '''TODO
        '''
        cls = self.get_class('RaggedIndexedContiguousArray')
        return cls(compressed_array=compressed_array, ndim=ndim,
                   shape=shape, size=size,
                   count_variable=count_variable,
                   index_variable=index_variable)

    def is_climatology(self, coordinate):
        '''TODO

    :Returns:

        `bool`
            The value of the 'climatology' cell extent parameter, or
            False if not set.

        '''
        return bool(coordinate.get_geometry(None) == 'climatology')

    def is_field(self, construct):
        '''Return True if the construct is a field construct

    :Parameters:

        construct: Construct

    :Returns:

        `bool`

        '''
        return getattr(construct, 'construct_type', None) == 'field'

    def is_geometry(self, coordinate):
        '''Return True if the coordinate bounds are geometries.

    :Parameters:

        coordinate:
            The coordinate construct.

    :Returns:

        `bool`
             True if the coordinate bounds are geometries, otherwise
             False.

        '''
        return bool(coordinate.get_geometry(None) in (
            'point', 'line', 'polygon'))

    def is_masked(self, data):
        '''Whether or not the data has any masked values.

    .. versionadded:: 1.8.0

    :Parameters:

        data: `Data`

    :Returns:

        `bool`
            Whether or not the data has any masked values.

        '''
        return data.mask.any()

    def nc_set_instance_dimension(self, variable, ncdim):
        '''TODO
        '''
        variable.nc_set_instance_dimension(ncdim)

    def nc_set_sample_dimension(self, variable, ncdim):
        '''TODO
        '''
        variable.nc_set_sample_dimension(ncdim)

    def set_auxiliary_coordinate(self, field, construct, axes, copy=True):
        '''Insert a auxiliary coordinate object into a field.

    :Parameters:

        field: `Field`

        construct: `AuxiliaryCoordinate`

        axes: `tuple`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, axes=axes, copy=copy)

    def set_bounds(self, construct, bounds, copy=True):
        '''TODO

    :Parameters:

    :Returns:

        `None`

        '''
        construct.set_bounds(bounds, copy=copy)

    def set_cell_measure(self, field, construct, axes, copy=True):
        '''Insert a cell_measure object into a field.

    :Parameters:

        field: `Field`

        construct: `CellMeasure`

        axes: `tuple`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, axes=axes, copy=copy)

    def set_cell_method(self, field, construct, copy=True):
        '''Insert a cell_method object into a field.

    :Parameters:

        field: `Field`

        construct: `CellMethod`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, copy=copy)

    def set_cell_method_axes(self, cell_method, axes):
        '''TODO
        '''
        cell_method.set_axes(axes)

    def set_cell_method_method(self, cell_method, method):
        '''TODO
        '''
        cell_method.set_method(method)

    def set_coordinate_conversion(self, coordinate_reference,
                                  coordinate_conversion):
        '''TODO

    :Parameters:

    :Returns:

        `None`

        '''
        coordinate_reference.set_coordinate_conversion(coordinate_conversion)

    def set_coordinate_reference(self, field, construct, copy=True):
        '''Insert a coordinate reference object into a field.

    :Parameters:
        field: `Field`

        construct: `CoordinateReference`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, copy=copy)

    def set_coordinate_reference_coordinates(self,
                                             coordinate_reference,
                                             coordinates):
        '''TODO

    :Parameters:

    :Returns:

        `None`
        '''
        coordinate_reference.set_coordinates(coordinates)

    def set_coordinate_reference_coordinate(self,
                                            coordinate_reference,
                                            coordinate):
        '''TODO
        '''
        coordinate_reference.set_coordinate(coordinate)

    def set_data(self, construct, data, axes=None, copy=True):
        '''If the construct is a Field then the corresponding domain
    axes must also be provided.

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
            construct.set_data(data, axes=axes, copy=copy)

    def set_datum(self, coordinate_reference, datum):
        '''Insert a datum object into a coordinate reference construct.

    :Parameters:

    :Returns:

        `None`

        '''
        coordinate_reference.set_datum(datum)

    def set_dimension_coordinate(self, field, construct, axes,
                                 copy=True):
        '''Insert a dimension coordinate object into a field.

    :Parameters:

        field: `Field`

        construct: `DimensionCoordinate`

        axes: `tuple`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, axes=axes, copy=copy)

    def set_domain_ancillary(self, field, construct, axes, copy=True):
        #                    extra_axes=0, copy=True):
        '''Insert a domain ancillary object into a field.

    :Parameters:

        field: `Field`

        construct: `DomainAncillary`

        axes: `tuple`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, axes=axes, copy=copy)

    def set_domain_axis(self, field, construct, copy=True):
        '''Insert a domain_axis object into a field.

    :Parameters:

        field: `Field`

        construct: `domain_axis`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, copy=copy)

    def nc_set_external(self, construct):
        '''TODO

        '''
        construct.nc_set_external(True)

    def set_field_ancillary(self, field, construct, axes, copy=True):
        '''Insert a field ancillary object into a field.

    :Parameters:

        field: `Field`

        construct: `FieldAncillary`

        axes: `tuple`

        copy: `bool`, optional

    :Returns:

        `str`

        '''
        return field.set_construct(construct, axes=axes, copy=copy)

    def set_geometry(self, coordinate, value):
        '''TODO

    .. versionadded:: 1.8.0

        '''
        coordinate.set_geometry(value)

    def set_node_count(self, parent, node_count, copy=True):
        '''Insert TODO

    Parameters:

       copy: `bool`, optional

    Returns:

       `None`
        '''
        parent.set_node_count(node_count, copy=copy)

    def set_part_node_count(self, parent, part_node_count, copy=True):
        '''Insert TODO

    .. versionadded:: 1.8.0

    :Parameters:

        copy: `bool`, optional

    :Returns:

        `None`
        '''
        parent.set_part_node_count(part_node_count, copy=copy)

    def set_interior_ring(self, parent, interior_ring, copy=True):
        '''Insert an interior ring array into a coordiante.

    .. versionadded:: 1.8.0

    :Parameters:

        copy: `bool`, optional

    :Returns:

        `None`

        '''
        parent.set_interior_ring(interior_ring, copy=copy)

    def set_dataset_compliance(self, field, report):
        '''TODO

    ..versionadded:: 1.7

        '''
        field._set_dataset_compliance(report)

    def nc_set_dimension(self, construct, ncdim):
        '''TODO

    :Parameters:

    :Returns:

        `None`

        '''
        construct.nc_set_dimension(ncdim)

    def nc_set_geometry_variable(self, field, ncvar):
        '''TODO

    :Parameters:

    :Returns:

        `None`

        '''
        field.nc_set_geometry_variable(ncvar)

    def nc_set_variable(self, parent, ncvar):
        '''TODO

    :Parameters:

    :Returns:

        `None`
        '''
        parent.nc_set_variable(ncvar)

    def nc_get_datum_variable(self, ref):
        '''TODO

    .. versionadded:: 1.7.5

    :Parameters:

    :Returns:

        `str` or `None`
        '''
        return ref.nc_get_datum_variable(default=None)

    def nc_set_datum_variable(self, ref, ncvar):
        '''TODO

    .. versionadded:: 1.7.5

    :Parameters:

    :Returns:

        `None`
        '''
        ref.nc_set_datum_variable(ncvar)

    def set_properties(self, construct, properties, copy=True):
        '''TODO

    :Parameters:

        construct:

        properties: `dict`

    :Returns:

        `None`

        '''
        construct.set_properties(properties, copy=copy)

    def has_bounds(self, construct):
        '''TODO

    :Parameters:

    :Returns:

        `bool`

        '''
        return construct.has_bounds()

    def has_datum(self, coordinate_reference):
        '''Return True if a coordinate reference has a datum.

    :Parameters:

        coordinate_reference: coordinate reference construct

    :Returns:

        `bool`

    **Examples:**

    >>> if API.has_datum(ref):
    ...     print ref, 'has a datum'
    ... else:
    ...     print ref, 'does not have a datum'

        '''
        return bool(coordinate_reference.datum)

    def has_property(self, parent, prop):
        '''Return True if a property exists.

    :Parameters:

        parent:
            The object containing the property.

    :Returns:

        `bool`
            `True` if the property exists, otherwise `False`.

    **Examples:**

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

    def squeeze(self, construct, axes=None):
        '''TODO
        '''
        return construct.squeeze(axes=axes)

# --- End: class


_implementation = CFDMImplementation(
    cf_version=CF(),

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
    InteriorRing=InteriorRing,

    CoordinateConversion=CoordinateConversion,
    Datum=Datum,

    List=List,
    Index=Index,
    Count=Count,
    NodeCountProperties=NodeCountProperties,
    PartNodeCountProperties=PartNodeCountProperties,

    Data=Data,
    GatheredArray=GatheredArray,
    NetCDFArray=NetCDFArray,
    RaggedContiguousArray=RaggedContiguousArray,
    RaggedIndexedArray=RaggedIndexedArray,
    RaggedIndexedContiguousArray=RaggedIndexedContiguousArray,
)


def implementation():
    '''Return a container for the CF data model implementation.

    .. versionadded:: 1.7.0

    .. seealso:: `cfdm.example_field`, `cfdm.read`, `cfdm.write`

    :Returns:

        `CFDMImplementation`
            A container for the CF data model implementation.

    **Examples:**

    >>> i = cfdm.implementation()
    >>> i
    <CFDMImplementation: >
    >>> i.classes()
    {'AuxiliaryCoordinate': cfdm.auxiliarycoordinate.AuxiliaryCoordinate,
     'Bounds': cfdm.bounds.Bounds,
     'CellMeasure': cfdm.cellmeasure.CellMeasure,
     'CellMethod': cfdm.cellmethod.CellMethod,
     'CoordinateConversion': cfdm.coordinateconversion.CoordinateConversion,
     'CoordinateReference': cfdm.coordinatereference.CoordinateReference,
     'Count': cfdm.count.Count,
     'Data': cfdm.data.data.Data,
     'Datum': cfdm.datum.Datum,
     'DimensionCoordinate': cfdm.dimensioncoordinate.DimensionCoordinate,
     'DomainAncillary': cfdm.domainancillary.DomainAncillary,
     'DomainAxis': cfdm.domainaxis.DomainAxis,
     'Field': cfdm.field.Field,
     'FieldAncillary': cfdm.fieldancillary.FieldAncillary,
     'GatheredArray': cfdm.data.gatheredarray.GatheredArray,
     'Index': cfdm.index.Index,
     'InteriorRing': cfdm.interiorring.InteriorRing,
     'List': cfdm.list.List,
     'NetCDFArray': cfdm.data.netcdfarray.NetCDFArray,
     'NodeCountProperties': cfdm.nodecount.NodeCountProperties,
     'PartNodeCountProperties': cfdm.partnodecount.PartNodeCountProperties,
     'RaggedContiguousArray': cfdm.data.raggedcontiguousarray.RaggedContiguousArray,
     'RaggedIndexedArray': cfdm.data.raggedindexedarray.RaggedIndexedArray,
     'RaggedIndexedContiguousArray': cfdm.data.raggedindexedcontiguousarray.RaggedIndexedContiguousArray}

    '''
    return _implementation.copy()
