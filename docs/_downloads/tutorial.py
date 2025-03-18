import cfdm
cfdm.log_level('INFO')
cfdm.CF()
x = cfdm.read('file.nc')
print(type(x))
len(x)
x
q = x[0]
t = x[1]
q
print(q)
print(t)
q.dump()
t.dump()
t.properties()
t.has_property('standard_name')
t.get_property('standard_name')
t.del_property('standard_name')
t.get_property('standard_name', default='not set')
t.set_property('standard_name', value='air_temperature')
t.get_property('standard_name', default='not set')
original = t.properties()
original
t.set_properties({'foo': 'bar', 'units': 'K'})
t.properties()
t.clear_properties()
t.properties()
t.set_properties(original)
t.properties()
t.coordinate_references()
print(t.coordinate_references())
list(t.coordinate_references().keys())
for key, value in t.coordinate_references().items():
    print(key, repr(value))
print(t.dimension_coordinates())
print(t.domain_axes())
q.constructs
print(q.constructs)
t.constructs
print(t.constructs)
t.data
print(t.array)
t.dtype
t.ndim
t.shape
t.size
t.data.size
print(t.domain_axes())
t
t.shape
t.get_data_axes()
data = t.del_data()
t.has_data()
t.set_data(data, axes=None)
t.data
d = cfdm.Data([1, 2, 3], units='days since 2004-2-28')
print(d.array)
print(d.datetime_array)
e = cfdm.Data([1, 2, 3], units='days since 2004-2-28',
              calendar='360_day')
print(e.array)
print(e.datetime_array)
q, t = cfdm.read('file.nc')
t
t2 = t.squeeze()
t2
print(t2.dimension_coordinates())
t3 = t2.insert_dimension(axis='domainaxis3', position=1)
t3
t3.transpose([2, 0, 1])
t4 = t.transpose([0, 2, 1], constructs=True)
print(q)
print(q.data.mask)
print(q.data.mask.array)
q.data[[0, 4], :] = cfdm.masked
print(q.data.mask.array)
q.data.mask.any()
cfdm.write(q, 'masked_q.nc')
no_mask_q = cfdm.read('masked_q.nc', mask=False)[0]
print(no_mask_q.array)
masked_q = no_mask_q.apply_masking()
print(masked_q.array)
data = t.data
data.shape
data[:, :, 1].shape
data[:, 0].shape
data[..., 6:3:-1, 3:6].shape
data[0, [2, 9], [4, 8]].shape
data[0, :, -2].shape
import numpy
t.data[:, 0, 0] = -1
t.data[:, :, 1] = -2
t.data[..., 6:3:-1, 3:6] = -3
print(t.array)
t.data[..., 6:3:-1, 3:6] = numpy.arange(9).reshape(3, 3)
t.data[0, [2, 9], [4, 8]] =  cfdm.Data([[-4, -5]])
print(t.array)
t.data[0, :, -2] = cfdm.masked
t.data[0, 5, -2] = -6
print(t.array)
print(q)
new = q[::-1, 0]
print(new)
print(q)
print(q.construct('longitude').data.array)
ind = q.indices(longitude=[112.5, 67.5])
print(ind)
print(q[ind])
print(q[q.indices(longitude=[112.5, 67.5], latitude=75)])
print(t.constructs.filter_by_type('dimension_coordinate'))
print(t.constructs.filter_by_type('cell_method', 'field_ancillary'))
print(t.constructs.filter_by_property(
            standard_name='air_temperature standard_error'))
print(t.constructs.filter_by_property(
            standard_name='air_temperature standard_error',
            units='K'))
print(t.constructs.filter_by_property(
            'or',
           standard_name='air_temperature standard_error',
            units='m'))
print(t.constructs.filter_by_axis('grid_latitude', 'grid_longitude',
                                  axis_mode='or'))
print(t.constructs.filter_by_measure('area'))
print(t.constructs.filter_by_method('maximum'))
print(
    t.constructs.filter_by_type('auxiliary_coordinate').filter_by_axis('domainaxis2')
)
c = t.constructs.filter_by_type('dimension_coordinate')
d = c.filter_by_property(units='degrees')
print(d)
c = t.constructs.filter(filter_by_type=('dimension_coordinate',),
                        filter_by_property={'units': 'degrees'})
print(c)
d = t.constructs.filter(filter_by_type=('dimension_coordinate',),
                        filter_by_property={'units': 'degrees'},
                        todict=True)
type(d)
print(d)
c = t.constructs.filter(filter_by_type=('dimension_coordinate',),
                        filter_by_property={'units': 'degrees'})
print(c)
print(t)
print(t.constructs.filter_by_identity('latitude'))
print(t.constructs.filter_by_identity('long_name=Grid latitude name'))
print(t.constructs.filter_by_identity('measure:area'))
print(t.constructs.filter_by_identity('ncvar%b'))
print(t.constructs.filter_by_identity('latitude'))
print(t.constructs('latitude'))
print(t.constructs.filter_by_key('domainancillary2'))
print(t.constructs.filter_by_key('cellmethod1'))
print(t.constructs.filter_by_key('auxiliarycoordinate2', 'cellmeasure0'))
c = t.constructs('radiation_wavelength')
c
print(c)
len(c)
c = t.constructs.filter_by_type('auxiliary_coordinate')
c
c.inverse_filter()
print(t.constructs.filter_by_type('cell_measure'))
print(t.cell_measures())
t.construct('latitude')
key = t.construct('latitude', key=True)
t.construct(key)
key, lat = t.construct('latitude', item=True)
key = t.construct('latitude', key=True)
t.constructs[key]
key = t.construct('latitude', key=True)
c = t.constructs.get(key)
c = t.constructs('latitude').value()
t.auxiliary_coordinate('latitude')
t.auxiliary_coordinate('latitude', key=True)
t.auxiliary_coordinate('latitude', item=True)
try:
    t.cell_measure('measure:volume')                # Raises Exception
except:
    pass
t.cell_measure('measure:volume', default=False)
try:
    t.cell_measure('measure:volume', default=Exception("my error"))  # Raises Exception
except:
    pass
c = t.cell_measures().filter_by_measure("volume")
len(c)
d = t.constructs("units=degrees")
len(d)
try:
    t.coordinate("units=degrees")  # Raises Exception
except:
    pass
print(t.coordinate("units=degrees", default=None))
lon = q.construct('longitude')
lon
lon.set_property('long_name', 'Longitude')
lon.properties()
area = t.construct('units=km2')
area
area.identity()
area.identities()
t.construct('measure:area')
lon = q.construct('longitude')
lon
lon.data
lon.data[2]
lon.data[2] = 133.33
print(lon.array)
t.get_data_axes('latitude')
t.constructs.data_axes()
time = q.construct('time')
time
time.get_property('units')
time.get_property('calendar', default='standard')
print(time.array)
print(time.datetime_array)
domain = t.domain
domain
print(domain)
description = domain.dump(display=False)
domain_latitude = t.domain.coordinate('latitude')
field_latitude = t.coordinate('latitude')
domain_latitude.set_property('test', 'set by domain')
print(field_latitude.get_property('test'))
field_latitude.set_property('test', 'set by field')
print(domain_latitude.get_property('test'))
domain_latitude.del_property('test')
field_latitude.has_property('test')
print(q.domain_axes())
d = q.domain_axes().get('domainaxis1')
d
d.get_size()
print(t.coordinates())
lon = t.coordinate('grid_longitude')
bounds = lon.bounds
bounds
bounds.data
print(bounds.array)
bounds.inherited_properties()
bounds.properties()
f = cfdm.read('geometry.nc')[0]
print(f)
lon = f.coordinate('longitude')
lon.dump()
lon.get_geometry()
print(lon.bounds.array)
print(lon.get_interior_ring().array)
f = cfdm.example_field(8)
print(f)
a = t.constructs.get('domainancillary0')
print(a.array)
bounds = a.bounds
bounds
print(bounds.array)
crs = t.coordinate_reference('standard_name:atmosphere_hybrid_height_coordinate')
crs
crs.dump()
crs.coordinates()
crs.datum
crs.datum.parameters()
crs.coordinate_conversion
crs.coordinate_conversion.parameters()
crs.coordinate_conversion.domain_ancillaries()
print(t.cell_methods())
cm = t.cell_method('method:mean')
cm
cm.get_axes()
cm.get_method()
cm.qualifiers()
cm.get_qualifier('where')
a = t.get_construct('fieldancillary0')
a
a.properties()
a.data
p = cfdm.Field(properties={'standard_name': 'precipitation_flux'})
p
dc = cfdm.DimensionCoordinate(properties={'long_name': 'Longitude'},
                              data=cfdm.Data([0, 1, 2.]))
dc
fa = cfdm.FieldAncillary(
       properties={'standard_name': 'precipitation_flux status_flag'},
       data=cfdm.Data(numpy.array([0, 0, 2], dtype='int8')))
fa
p = cfdm.Field()
p
p.set_property('standard_name', 'precipitation_flux')
p
dc = cfdm.DimensionCoordinate()
dc
dc.set_property('long_name', 'Longitude')
dc.set_data(cfdm.Data([1, 2, 3.]))
dc
fa = cfdm.FieldAncillary(
       data=cfdm.Data(numpy.array([0, 0, 2], dtype='int8')))
fa
fa.set_property('standard_name', 'precipitation_flux status_flag')
fa
longitude_axis = p.set_construct(cfdm.DomainAxis(3))
longitude_axis
key = p.set_construct(dc, axes=longitude_axis)
key
cm = cfdm.CellMethod(axes=longitude_axis, method='minimum')
p.set_construct(cm)
# Start of code block

import numpy
import cfdm

# Initialise the field construct with properties
Q = cfdm.Field(
properties={'project': 'research',
'standard_name': 'specific_humidity',
'units': '1'})

# Create the domain axis constructs
domain_axisT = cfdm.DomainAxis(1)
domain_axisY = cfdm.DomainAxis(5)
domain_axisX = cfdm.DomainAxis(8)

# Insert the domain axis constructs into the field. The
# set_construct method returns the domain axis construct key that
# will be used later to specify which domain axis corresponds to
# which dimension coordinate construct.
axisT = Q.set_construct(domain_axisT)
axisY = Q.set_construct(domain_axisY)
axisX = Q.set_construct(domain_axisX)

# Create and insert the field construct data
data = cfdm.Data(numpy.arange(40.).reshape(5, 8))
Q.set_data(data, axes=[axisY, axisX])

# Create the cell method constructs
cell_method1 = cfdm.CellMethod(axes='area', method='mean')

cell_method2 = cfdm.CellMethod()
cell_method2.set_axes(axisT)
cell_method2.set_method('maximum')

# Insert the cell method constructs into the field in the same
# order that their methods were applied to the data
Q.set_construct(cell_method1)
Q.set_construct(cell_method2)

# Create a "time" dimension coordinate construct, with coordinate
# bounds
dimT = cfdm.DimensionCoordinate(
properties={'standard_name': 'time',
'units': 'days since 2018-12-01'},
data=cfdm.Data([15.5]),
bounds=cfdm.Bounds(data=cfdm.Data([[0,31.]])))

# Create a "longitude" dimension coordinate construct, without
# coordinate bounds
dimX = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(8.)))
dimX.set_properties({'standard_name': 'longitude',
'units': 'degrees_east'})

# Create a "longitude" dimension coordinate construct
dimY = cfdm.DimensionCoordinate(properties={'standard_name': 'latitude',
'units': 'degrees_north'})
array = numpy.arange(5.)
dimY.set_data(cfdm.Data(array))

# Create and insert the latitude coordinate bounds
bounds_array = numpy.empty((5, 2))
bounds_array[:, 0] = array - 0.5
bounds_array[:, 1] = array + 0.5
bounds = cfdm.Bounds(data=cfdm.Data(bounds_array))
dimY.set_bounds(bounds)

# Insert the dimension coordinate constructs into the field,
# specifying to # which domain axis each one corresponds
Q.set_construct(dimT, axes=axisT)
Q.set_construct(dimY, axes=axisY)
Q.set_construct(dimX, axes=axisX)

# End of code block
Q.dump()
# Start of code block

import numpy
import cfdm

# Initialise the field construct
tas = cfdm.Field(
properties={'project': 'research',
'standard_name': 'air_temperature',
'units': 'K'})

# Create and set domain axis constructs
axis_T = tas.set_construct(cfdm.DomainAxis(1))
axis_Z = tas.set_construct(cfdm.DomainAxis(1))
axis_Y = tas.set_construct(cfdm.DomainAxis(10))
axis_X = tas.set_construct(cfdm.DomainAxis(9))

# Set the field construct data
tas.set_data(cfdm.Data(numpy.arange(90.).reshape(10, 9)),
axes=[axis_Y, axis_X])

# Create and set the cell method constructs
cell_method1 = cfdm.CellMethod(
axes=[axis_Y, axis_X],
method='mean',
qualifiers={'where': 'land',
'interval': [cfdm.Data(0.1, units='degrees')]})

cell_method2 = cfdm.CellMethod(axes=axis_T, method='maximum')

tas.set_construct(cell_method1)
tas.set_construct(cell_method2)

# Create and set the field ancillary constructs
field_ancillary = cfdm.FieldAncillary(
properties={'standard_name': 'air_temperature standard_error',
'units': 'K'},
data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

tas.set_construct(field_ancillary, axes=[axis_Y, axis_X])

# Create and set the dimension coordinate constructs
dimension_coordinate_T = cfdm.DimensionCoordinate(
properties={'standard_name': 'time',
'units': 'days since 2018-12-01'},
data=cfdm.Data([15.5]),
bounds=cfdm.Bounds(data=cfdm.Data([[0., 31]])))

dimension_coordinate_Z = cfdm.DimensionCoordinate(
properties={'computed_standard_name': 'altitude',
'standard_name': 'atmosphere_hybrid_height_coordinate'},
data = cfdm.Data([1.5]),
bounds=cfdm.Bounds(data=cfdm.Data([[1.0, 2.0]])))

dimension_coordinate_Y = cfdm.DimensionCoordinate(
properties={'standard_name': 'grid_latitude',
'units': 'degrees'},
data=cfdm.Data(numpy.arange(10.)),
bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(20).reshape(10, 2))))

dimension_coordinate_X = cfdm.DimensionCoordinate(
properties={'standard_name': 'grid_longitude',
'units': 'degrees'},
data=cfdm.Data(numpy.arange(9.)),
bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(18).reshape(9, 2))))

dim_T = tas.set_construct(dimension_coordinate_T, axes=axis_T)
dim_Z = tas.set_construct(dimension_coordinate_Z, axes=axis_Z)
dim_Y = tas.set_construct(dimension_coordinate_Y, axes=axis_Y)
dim_X = tas.set_construct(dimension_coordinate_X, axes=axis_X)

# Create and set the auxiliary coordinate constructs
auxiliary_coordinate_lat = cfdm.AuxiliaryCoordinate(
properties={'standard_name': 'latitude',
'units': 'degrees_north'},
data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

auxiliary_coordinate_lon = cfdm.AuxiliaryCoordinate(
properties={'standard_name': 'longitude',
'units': 'degrees_east'},
data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))

array = numpy.ma.array(list('abcdefghij'))
array[0] = numpy.ma.masked
auxiliary_coordinate_name = cfdm.AuxiliaryCoordinate(
properties={'long_name': 'Grid latitude name'},
data=cfdm.Data(array))

aux_LAT  = tas.set_construct(auxiliary_coordinate_lat, axes=[axis_Y, axis_X])
aux_LON  = tas.set_construct(auxiliary_coordinate_lon, axes=[axis_X, axis_Y])
aux_NAME = tas.set_construct(auxiliary_coordinate_name, axes=[axis_Y])

# Create and set domain ancillary constructs
domain_ancillary_a = cfdm.DomainAncillary(
properties={'units': 'm'},
data=cfdm.Data([10.]),
bounds=cfdm.Bounds(data=cfdm.Data([[5., 15.]])))

domain_ancillary_b = cfdm.DomainAncillary(
properties={'units': '1'},
data=cfdm.Data([20.]),
bounds=cfdm.Bounds(data=cfdm.Data([[14, 26.]])))

domain_ancillary_orog = cfdm.DomainAncillary(
properties={'standard_name': 'surface_altitude',
'units': 'm'},
data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

domain_anc_A = tas.set_construct(domain_ancillary_a, axes=axis_Z)
domain_anc_B = tas.set_construct(domain_ancillary_b, axes=axis_Z)
domain_anc_OROG = tas.set_construct(domain_ancillary_orog,
axes=[axis_Y, axis_X])

# Create the datum for the coordinate reference constructs
datum = cfdm.Datum(parameters={'earth_radius': 6371007.})

# Create the coordinate conversion for the horizontal coordinate
# reference construct
coordinate_conversion_h = cfdm.CoordinateConversion(
parameters={'grid_mapping_name': 'rotated_latitude_longitude',
'grid_north_pole_latitude': 38.0,
'grid_north_pole_longitude': 190.0})

# Create the coordinate conversion for the vertical coordinate
# reference construct
coordinate_conversion_v = cfdm.CoordinateConversion(
parameters={'standard_name': 'atmosphere_hybrid_height_coordinate',
'computed_standard_name': 'altitude'},
domain_ancillaries={'a': domain_anc_A,
'b': domain_anc_B,
'orog': domain_anc_OROG})

# Create the vertical coordinate reference construct
horizontal_crs = cfdm.CoordinateReference(
datum=datum,
coordinate_conversion=coordinate_conversion_h,
coordinates=[dim_X,
dim_Y,
aux_LAT,
aux_LON])

# Create the vertical coordinate reference construct
vertical_crs = cfdm.CoordinateReference(
datum=datum,
coordinate_conversion=coordinate_conversion_v,
coordinates=[dim_Z])

# Set the coordinate reference constructs
tas.set_construct(horizontal_crs)
tas.set_construct(vertical_crs)

# Create and set the cell measure constructs
cell_measure = cfdm.CellMeasure(measure='area',
properties={'units': 'km2'},
data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))

tas.set_construct(cell_measure, axes=[axis_X, axis_Y])

# End of code block
print(tas)
q, t = cfdm.read('file.nc')
print(q.creation_commands())
import netCDF4
nc = netCDF4.Dataset('file.nc', 'r')
v = nc.variables['ta']
netcdf_array = cfdm.NetCDF4Array(filename='file.nc', address='ta',
                                dtype=v.dtype, shape=v.shape)
data_disk = cfdm.Data(netcdf_array)
numpy_array = v[...]
data_memory = cfdm.Data(numpy_array)
data_disk.equals(data_memory)
orog = tas.convert('surface_altitude')
print(orog)
orog1 = tas.convert('surface_altitude', full_domain=False)
print(orog1)
cfdm.write(tas, 'tas.nc')
f = cfdm.read('tas.nc')
f
fields = cfdm.read('tas.nc', extra='domain_ancillary')
fields
orog_from_file = fields[3]
print(orog_from_file)
u = t.copy()
u.data[0, 0, 0] = -1e30
u.data[0, 0, 0]
t.data[0, 0, 0]
u.del_construct('grid_latitude')
u.constructs('grid_latitude')
t.constructs('grid_latitude')
import copy
u = copy.deepcopy(t)
orog = t.domain_ancillary('surface_altitude').copy()
t.equals(t)
t.equals(t.copy())
t.equals(t[...])
t.equals(q)
t.equals(q, verbose=True)
print(cfdm.atol())
print(cfdm.rtol())
original = cfdm.rtol(0.00001)
print(cfdm.rtol())
print(cfdm.rtol(original))
print(cfdm.rtol())
print(cfdm.atol())
with cfdm.atol(1e-5):
    print(cfdm.atol())
print(cfdm.atol())
orog = t.domain_ancillary('surface_altitude')
orog.equals(orog.copy())
print(t.constructs.filter_by_ncvar('b'))
t.construct('ncvar%x')
t.construct('ncdim%x')
q.nc_get_variable()
q.nc_global_attributes()
q.nc_set_variable('humidity')
q.nc_get_variable()
q.construct('latitude').nc_get_variable()
print(q)
cfdm.write(q, 'q_file.nc')
x
cfdm.write(x, 'new_file.nc')
g = cfdm.example_field(2)
cfdm.write(g, 'append-example-file.nc')
cfdm.read('append-example-file.nc')
h = cfdm.example_field(0)
h
cfdm.write(h, 'append-example-file.nc', mode='a')
cfdm.read('append-example-file.nc')
f = cfdm.read('q_file.nc')[0]
q.equals(f)
f.set_property('model', 'model_A')
cfdm.write(f, 'f_file.nc', global_attributes='model')
f.nc_global_attributes()
f.nc_set_global_attribute('model')
f.nc_global_attributes()
f.nc_global_attributes(values=True)
cfdm.write(f, 'f_file.nc')
f.set_property('information', 'variable information')
f.properties()
f.nc_set_global_attribute('information', 'global information')
f.nc_global_attributes()
cfdm.write(f, 'f_file.nc')
cfdm.write(f, 'f_file.nc', file_descriptors={'history': 'created today'})
f_file = cfdm.read('f_file.nc')[0]
f_file.properties()
f_file.nc_global_attributes()
f_file.set_property('Conventions', 'UGRID-1.0')
cfdm.write(f, 'f_file.nc', Conventions='UGRID-1.0')
print(q)
axes = q.get_data_axes('time')
axes
q2 = q.insert_dimension(axis=axes[0])
q2
cfdm.write(q2, 'q2_file.nc')
q, t = cfdm.read('file.nc')
print(q)
q.set_property('comment', 'comment')
q.nc_set_group_attribute('comment', 'group comment')
q.nc_set_variable_groups(['forecast', 'model'])
q.construct('time').nc_set_variable_groups(['forecast'])
cfdm.write(q, 'grouped.nc')
g = cfdm.read('grouped.nc')[0]
print(g)
g.nc_get_variable()
g.nc_variable_groups()
g.nc_group_attributes(values=True)
g.construct('latitude').nc_get_variable()
cfdm.write(g, 'flat.nc', group=False)
f = cfdm.read('flat.nc')[0]
f.equals(g)
u = cfdm.read('parent.nc')[0]
print(u)
area = u.cell_measure('measure:area')
area
area.nc_get_external()
area.nc_get_variable()
area.properties()
area.has_data()
g = cfdm.read('parent.nc', external='external.nc')[0]
print(g)
area = g.cell_measure('measure:area')
area
area.nc_get_external()
area.nc_get_variable()
area.properties()
area.data
area.nc_set_external(True)
cfdm.write(g, 'new_parent.nc')
cfdm.write(g, 'new_parent.nc', external='new_external.nc')
h = cfdm.read('contiguous.nc')[0]
print(h)
print(h.array)
h.data.get_compression_type()
print(h.data.compressed_array)
count_variable = h.data.get_count()
count_variable
print(count_variable.array)
station2 = h[1]
station2
print(station2.array)
h.data.get_compression_type()
h.data[1, 2] = -9
print(h.array)
h.data.get_compression_type()
# Start of code block

import numpy
import cfdm

# Define the array values
data = cfdm.Data([[280.0,-99,   -99,   -99],
[281.0, 279.0, 278.0, 279.5]],
mask=[[0, 1, 1, 1],
[0, 0, 0, 0]])

# Create the field construct
T = cfdm.Field()
T.set_properties({'standard_name': 'air_temperature',
'units': 'K',
'featureType': 'timeSeries'})

# Create the domain axis constructs
X = T.set_construct(cfdm.DomainAxis(4))
Y = T.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
T.set_data(data, axes=[Y, X])

# Compress the data
T.compress('contiguous',
count_properties={'long_name': 'number of obs for this timeseries'},
inplace=True)

# End of code block
T
print(T.array)
T.data.get_compression_type()
print(T.data.compressed_array)
count_variable = T.data.get_count()
count_variable
print(count_variable.array)
cfdm.write(T, 'T_contiguous.nc')
# Start of code block

import numpy
import cfdm

# Define the ragged array values
ragged_array = cfdm.Data([280, 281, 279, 278, 279.5])

# Define the count array values
count_array = [1, 4]

# Create the count variable
count_variable = cfdm.Count(data=cfdm.Data(count_array))
count_variable.set_property('long_name', 'number of obs for this timeseries')

# Create the contiguous ragged array object, specifying the
# uncompressed shape
array = cfdm.RaggedContiguousArray(
compressed_array=ragged_array,
shape=(2, 4),
count_variable=count_variable)

# Create the field construct with the domain axes and the ragged
# array
T = cfdm.Field()
T.set_properties({'standard_name': 'air_temperature',
'units': 'K',
'featureType': 'timeSeries'})

# Create the domain axis constructs for the uncompressed array
X = T.set_construct(cfdm.DomainAxis(4))
Y = T.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
T.set_data(cfdm.Data(array), axes=[Y, X])

# End of code block
p = cfdm.read('gathered.nc')[0]
print(p)
print(p.array)
p.data.get_compression_type()
print(p.data.compressed_array)
list_variable = p.data.get_list()
list_variable
print(list_variable.array)
p[0]
p[1, :, 3:5]
p.data.get_compression_type()
p.data[1] = -9
p.data.get_compression_type()
# Start of code block

import numpy
import cfdm

# Define the gathered values
gathered_array = cfdm.Data([[2, 1, 3], [4, 0, 5]])

# Define the list array values
list_array = [1, 4, 5]

# Create the list variable
list_variable = cfdm.List(data=cfdm.Data(list_array))

# Create the gathered array object, specifying the uncompressed
# shape
array = cfdm.GatheredArray(
compressed_array=gathered_array,
compressed_dimensions={1: (1, 2)},
shape=(2, 3, 2),
list_variable=list_variable)

# Create the field construct with the domain axes and the gathered
# array
P = cfdm.Field(properties={'standard_name': 'precipitation_flux',
'units': 'kg m-2 s-1'})

# Create the domain axis constructs for the uncompressed array
T = P.set_construct(cfdm.DomainAxis(2))
Y = P.set_construct(cfdm.DomainAxis(3))
X = P.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
P.set_data(cfdm.Data(array), axes=[T, Y, X])

# End of code block
P
print(P.array)
P.data.get_compression_type()
print(P.data.compressed_array)
list_variable = P.data.get_list()
list_variable
print(list_variable.array)
cfdm.write(P, 'P_gathered.nc')
f = cfdm.read('subsampled.nc')[0]
print(f)
lon = f.construct('longitude')
lon
lon.data.source()
print(lon.array)
lon.data.source().source()
print(lon.data.source().source().array)
g = f[0, 6, :]
print(g)
print(g.construct('longitude').array)
lon = f.construct('longitude')
d = lon.data.source()
d.get_tie_point_indices()
d.get_computational_precision()
