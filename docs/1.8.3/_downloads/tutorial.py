print("\n**Tutorial**\n")


print("\n**Import**\n")

import cfdm

cfdm.CF()

print("\n**Field construct**\n")


print("\n**Reading field constructs from datasets**\n")

x = cfdm.read("file.nc")
print(type(x))
len(x)

print("\n**Inspection**\n")

x
q = x[0]
t = x[1]
q
print(q)
print(t)
q.dump()
t.dump()

print("\n**Properties**\n")

t.properties()
t.has_property("standard_name")
t.get_property("standard_name")
t.del_property("standard_name")
t.get_property("standard_name", default="not set")
t.set_property("standard_name", value="air_temperature")
t.get_property("standard_name", default="not set")
original = t.properties()
original
t.set_properties({"foo": "bar", "units": "K"})
t.properties()
t.clear_properties()
t.properties()
t.set_properties(original)
t.properties()

print("\n**Metadata constructs**\n")

t.coordinate_references
print(t.coordinate_references)
list(t.coordinate_references.keys())
for key, value in t.coordinate_references.items():
    print(key, repr(value))

print(t.dimension_coordinates)
print(t.domain_axes)
q.constructs
print(q.constructs)
t.constructs
print(t.constructs)

print("\n**Data**\n")

t.data
print(t.data.array)
t.dtype
t.ndim
t.shape
t.size
t.data.size
print(t.domain_axes)
t
t.shape
t.get_data_axes()
data = t.del_data()
t.has_data()
t.set_data(data, axes=None)
t.data
d = cfdm.Data([1, 2, 3], units="days since 2004-2-28")
print(d.array)
print(d.datetime_array)
e = cfdm.Data([1, 2, 3], units="days since 2004-2-28", calendar="360_day")
print(e.array)
print(e.datetime_array)
q, t = cfdm.read("file.nc")
t
t2 = t.squeeze()
t2
print(t2.dimension_coordinates)
t3 = t2.insert_dimension(axis="domainaxis3", position=1)
t3
t3.transpose([2, 0, 1])
t4 = t.transpose([0, 2, 1], constructs=True)
print(q)
print(q.data.mask)
print(q.data.mask.array)
q.data[[0, 4], :] = cfdm.masked
print(q.data.mask.array)
q.data.mask.any()
cfdm.write(q, "masked_q.nc")
no_mask_q = cfdm.read("masked_q.nc", mask=False)[0]
print(no_mask_q.data.array)
masked_q = no_mask_q.apply_masking()
print(masked_q.data.array)
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
print(t.data.array)
t.data[..., 6:3:-1, 3:6] = numpy.arange(9).reshape(3, 3)
t.data[0, [2, 9], [4, 8]] = cfdm.Data([[-4, -5]])
print(t.data.array)
t.data[0, :, -2] = cfdm.masked
t.data[0, 5, -2] = -6
print(t.data.array)
t
t2 = t.squeeze()
t2
print(t2.dimension_coordinates)
t3 = t2.insert_dimension(axis="domainaxis3", position=1)
t3
t3.transpose([2, 0, 1])

print("\n**Subspacing**\n")

print(q)
new = q[::-1, 0]
print(new)

print("\n**Filtering metadata constructs**\n")

print(t.constructs.filter_by_type("dimension_coordinate"))
print(t.constructs.filter_by_type("cell_method", "field_ancillary"))
print(
    t.constructs.filter_by_property(
        standard_name="air_temperature standard_error"
    )
)
print(
    t.constructs.filter_by_property(
        standard_name="air_temperature standard_error", units="K"
    )
)
print(
    t.constructs.filter_by_property(
        "or", standard_name="air_temperature standard_error", units="m"
    )
)
print(t.constructs.filter_by_axis("and", "domainaxis1"))
print(t.constructs.filter_by_measure("area"))
print(t.constructs.filter_by_method("maximum"))
print(
    t.constructs.filter_by_type("auxiliary_coordinate").filter_by_axis(
        "and", "domainaxis2"
    )
)
c = t.constructs.filter_by_type("dimension_coordinate")
d = c.filter_by_property(units="degrees")
print(d)
print(t)
print(t.constructs.filter_by_identity("latitude"))
print(t.constructs.filter_by_identity("long_name=Grid latitude name"))
print(t.constructs.filter_by_identity("measure:area"))
print(t.constructs.filter_by_identity("ncvar%b"))
print(t.constructs.filter_by_identity("latitude"))
print(t.constructs("latitude"))
print(t.constructs.filter_by_key("domainancillary2"))
print(t.constructs.filter_by_key("cellmethod1"))
print(t.constructs.filter_by_key("auxiliarycoordinate2", "cellmeasure0"))
c = t.constructs("radiation_wavelength")
c
print(c)
len(c)
c = t.constructs.filter_by_type("auxiliary_coordinate")
c
c.inverse_filter()
print(t.constructs.filter_by_type("cell_measure"))
print(t.cell_measures)

print("\n**Metadata construct access**\n")

t.construct("latitude")
key = t.construct_key("latitude")
t.get_construct(key)
t.constructs("latitude").value()
c = t.constructs.get(key)
t.constructs[key]
try:
    t.construct("measure:volume")
except:
    pass
else:
    raise Exception("This should have failed!")

t.construct("measure:volume", False)
c = t.constructs.filter_by_measure("volume")
len(c)
try:
    c.value()
except:
    pass
else:
    raise Exception("This should have failed!")

c.value(default="No construct")
try:
    c.value(default=KeyError("My message"))
except:
    pass
else:
    raise Exception("This should have failed!")

d = t.constructs("units=degrees")
len(d)
try:
    d.value()
except:
    pass
else:
    raise Exception("This should have failed!")

print(d.value(default=None))
lon = q.construct("longitude")
lon
lon.set_property("long_name", "Longitude")
lon.properties()
area = t.constructs.filter_by_property(units="km2").value()
area
area.identity()
area.identities()
lon = q.constructs("longitude").value()
lon
lon.data
lon.data[2]
lon.data[2] = 133.33
print(lon.data.array)
key = t.construct_key("latitude")
key
t.get_data_axes(key=key)
t.constructs.data_axes()

print("\n**Time**\n")

time = q.construct("time")
time
time.get_property("units")
time.get_property("calendar", default="standard")
print(time.data.array)
print(time.data.datetime_array)

print("\n**Domain**\n")

domain = t.domain
domain
print(domain)
description = domain.dump(display=False)
domain_latitude = t.domain.constructs("latitude").value()
field_latitude = t.constructs("latitude").value()
domain_latitude.set_property("test", "set by domain")
print(field_latitude.get_property("test"))
field_latitude.set_property("test", "set by field")
print(domain_latitude.get_property("test"))
domain_latitude.del_property("test")
field_latitude.has_property("test")

print("\n**Domain axes**\n")

print(q.domain_axes)
d = q.domain_axes.get("domainaxis1")
d
d.get_size()

print("\n**Coordinates**\n")

print(t.coordinates)
lon = t.constructs("grid_longitude").value()
bounds = lon.bounds
bounds
bounds.data
print(bounds.data.array)
bounds.inherited_properties()
bounds.properties()
f = cfdm.read("geometry.nc")[0]
print(f)
lon = f.construct("longitude")
lon.dump()
lon.get_geometry()
print(lon.bounds.data.array)
print(lon.get_interior_ring().data.array)

print("\n**Domain ancillaries**\n")

a = t.constructs.get("domainancillary0")
print(a.data.array)
bounds = a.bounds
bounds
print(bounds.data.array)

print("\n**Coordinate systems**\n")

crs = t.constructs("standard_name:atmosphere_hybrid_height_coordinate").value()
crs
crs.dump()
crs.coordinates()
crs.datum
crs.datum.parameters()
crs.coordinate_conversion
crs.coordinate_conversion.parameters()
crs.coordinate_conversion.domain_ancillaries()

print("\n**Cell methods**\n")

print(t.cell_methods)
t.cell_methods.ordered()
cm = t.constructs("method:mean").value()
cm
cm.get_axes()
cm.get_method()
cm.qualifiers()
cm.get_qualifier("where")

print("\n**Field ancillaries**\n")

a = t.get_construct("fieldancillary0")
a
a.properties()
a.data

print("\n**Field creation**\n")


print("\n**Stage 1:** The field construct is created without metadata\n")


print("\n**Stage 2:** Metadata constructs are created independently.\n")


print("\n**Stage 3:** The metadata constructs are inserted into the field\n")

p = cfdm.Field(properties={"standard_name": "precipitation_flux"})
p
dc = cfdm.DimensionCoordinate(
    properties={"long_name": "Longitude"}, data=cfdm.Data([0, 1, 2.0])
)
dc
fa = cfdm.FieldAncillary(
    properties={"standard_name": "precipitation_flux status_flag"},
    data=cfdm.Data(numpy.array([0, 0, 2], dtype="int8")),
)
fa
p = cfdm.Field()
p
p.set_property("standard_name", "precipitation_flux")
p
dc = cfdm.DimensionCoordinate()
dc
dc.set_property("long_name", "Longitude")
dc.set_data(cfdm.Data([1, 2, 3.0]))
dc
fa = cfdm.FieldAncillary(data=cfdm.Data(numpy.array([0, 0, 2], dtype="int8")))
fa
fa.set_property("standard_name", "precipitation_flux status_flag")
fa
longitude_axis = p.set_construct(cfdm.DomainAxis(3))
longitude_axis
key = p.set_construct(dc, axes=longitude_axis)
key
cm = cfdm.CellMethod(axes=longitude_axis, method="minimum")
p.set_construct(cm)

import numpy
import cfdm

# Initialise the field construct with properties
Q = cfdm.Field(
    properties={
        "project": "research",
        "standard_name": "specific_humidity",
        "units": "1",
    }
)

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
data = cfdm.Data(numpy.arange(40.0).reshape(5, 8))
Q.set_data(data, axes=[axisY, axisX])

# Create the cell method constructs
cell_method1 = cfdm.CellMethod(axes="area", method="mean")

cell_method2 = cfdm.CellMethod()
cell_method2.set_axes(axisT)
cell_method2.set_method("maximum")

# Insert the cell method constructs into the field in the same
# order that their methods were applied to the data
Q.set_construct(cell_method1)
Q.set_construct(cell_method2)

# Create a "time" dimension coordinate construct, with coordinate
# bounds
dimT = cfdm.DimensionCoordinate(
    properties={"standard_name": "time", "units": "days since 2018-12-01"},
    data=cfdm.Data([15.5]),
    bounds=cfdm.Bounds(data=cfdm.Data([[0, 31.0]])),
)

# Create a "longitude" dimension coordinate construct, without
# coordinate bounds
dimX = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(8.0)))
dimX.set_properties({"standard_name": "longitude", "units": "degrees_east"})

# Create a "longitude" dimension coordinate construct
dimY = cfdm.DimensionCoordinate(
    properties={"standard_name": "latitude", "units": "degrees_north"}
)
array = numpy.arange(5.0)
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

Q.dump()

import numpy
import cfdm

# Initialize the field construct
tas = cfdm.Field(
    properties={
        "project": "research",
        "standard_name": "air_temperature",
        "units": "K",
    }
)

# Create and set domain axis constructs
axis_T = tas.set_construct(cfdm.DomainAxis(1))
axis_Z = tas.set_construct(cfdm.DomainAxis(1))
axis_Y = tas.set_construct(cfdm.DomainAxis(10))
axis_X = tas.set_construct(cfdm.DomainAxis(9))

# Set the field construct data
tas.set_data(
    cfdm.Data(numpy.arange(90.0).reshape(10, 9)), axes=[axis_Y, axis_X]
)

# Create and set the cell method constructs
cell_method1 = cfdm.CellMethod(
    axes=[axis_Y, axis_X],
    method="mean",
    qualifiers={
        "where": "land",
        "interval": [cfdm.Data(0.1, units="degrees")],
    },
)

cell_method2 = cfdm.CellMethod(axes=axis_T, method="maximum")

tas.set_construct(cell_method1)
tas.set_construct(cell_method2)

# Create and set the field ancillary constructs
field_ancillary = cfdm.FieldAncillary(
    properties={
        "standard_name": "air_temperature standard_error",
        "units": "K",
    },
    data=cfdm.Data(numpy.arange(90.0).reshape(10, 9)),
)

tas.set_construct(field_ancillary, axes=[axis_Y, axis_X])

# Create and set the dimension coordinate constructs
dimension_coordinate_T = cfdm.DimensionCoordinate(
    properties={"standard_name": "time", "units": "days since 2018-12-01"},
    data=cfdm.Data([15.5]),
    bounds=cfdm.Bounds(data=cfdm.Data([[0.0, 31]])),
)

dimension_coordinate_Z = cfdm.DimensionCoordinate(
    properties={
        "computed_standard_name": "altitude",
        "standard_name": "atmosphere_hybrid_height_coordinate",
    },
    data=cfdm.Data([1.5]),
    bounds=cfdm.Bounds(data=cfdm.Data([[1.0, 2.0]])),
)

dimension_coordinate_Y = cfdm.DimensionCoordinate(
    properties={"standard_name": "grid_latitude", "units": "degrees"},
    data=cfdm.Data(numpy.arange(10.0)),
    bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(20).reshape(10, 2))),
)

dimension_coordinate_X = cfdm.DimensionCoordinate(
    properties={"standard_name": "grid_longitude", "units": "degrees"},
    data=cfdm.Data(numpy.arange(9.0)),
    bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(18).reshape(9, 2))),
)

dim_T = tas.set_construct(dimension_coordinate_T, axes=axis_T)
dim_Z = tas.set_construct(dimension_coordinate_Z, axes=axis_Z)
dim_Y = tas.set_construct(dimension_coordinate_Y, axes=axis_Y)
dim_X = tas.set_construct(dimension_coordinate_X, axes=axis_X)

# Create and set the auxiliary coordinate constructs
auxiliary_coordinate_lat = cfdm.AuxiliaryCoordinate(
    properties={"standard_name": "latitude", "units": "degrees_north"},
    data=cfdm.Data(numpy.arange(90.0).reshape(10, 9)),
)

auxiliary_coordinate_lon = cfdm.AuxiliaryCoordinate(
    properties={"standard_name": "longitude", "units": "degrees_east"},
    data=cfdm.Data(numpy.arange(90.0).reshape(9, 10)),
)

array = numpy.ma.array(list("abcdefghij"))
array[0] = numpy.ma.masked
auxiliary_coordinate_name = cfdm.AuxiliaryCoordinate(
    properties={"long_name": "Grid latitude name"}, data=cfdm.Data(array)
)

aux_LAT = tas.set_construct(auxiliary_coordinate_lat, axes=[axis_Y, axis_X])
aux_LON = tas.set_construct(auxiliary_coordinate_lon, axes=[axis_X, axis_Y])
aux_NAME = tas.set_construct(auxiliary_coordinate_name, axes=[axis_Y])

# Create and set domain ancillary constructs
domain_ancillary_a = cfdm.DomainAncillary(
    properties={"units": "m"},
    data=cfdm.Data([10.0]),
    bounds=cfdm.Bounds(data=cfdm.Data([[5.0, 15.0]])),
)

domain_ancillary_b = cfdm.DomainAncillary(
    properties={"units": "1"},
    data=cfdm.Data([20.0]),
    bounds=cfdm.Bounds(data=cfdm.Data([[14, 26.0]])),
)

domain_ancillary_orog = cfdm.DomainAncillary(
    properties={"standard_name": "surface_altitude", "units": "m"},
    data=cfdm.Data(numpy.arange(90.0).reshape(10, 9)),
)

domain_anc_A = tas.set_construct(domain_ancillary_a, axes=axis_Z)
domain_anc_B = tas.set_construct(domain_ancillary_b, axes=axis_Z)
domain_anc_OROG = tas.set_construct(
    domain_ancillary_orog, axes=[axis_Y, axis_X]
)

# Create the datum for the coordinate reference constructs
datum = cfdm.Datum(parameters={"earth_radius": 6371007.0})

# Create the coordinate conversion for the horizontal coordinate
# reference construct
coordinate_conversion_h = cfdm.CoordinateConversion(
    parameters={
        "grid_mapping_name": "rotated_latitude_longitude",
        "grid_north_pole_latitude": 38.0,
        "grid_north_pole_longitude": 190.0,
    }
)

# Create the coordinate conversion for the vertical coordinate
# reference construct
coordinate_conversion_v = cfdm.CoordinateConversion(
    parameters={
        "standard_name": "atmosphere_hybrid_height_coordinate",
        "computed_standard_name": "altitude",
    },
    domain_ancillaries={
        "a": domain_anc_A,
        "b": domain_anc_B,
        "orog": domain_anc_OROG,
    },
)

# Create the vertical coordinate reference construct
horizontal_crs = cfdm.CoordinateReference(
    datum=datum,
    coordinate_conversion=coordinate_conversion_h,
    coordinates=[dim_X, dim_Y, aux_LAT, aux_LON],
)

# Create the vertical coordinate reference construct
vertical_crs = cfdm.CoordinateReference(
    datum=datum,
    coordinate_conversion=coordinate_conversion_v,
    coordinates=[dim_Z],
)

# Set the coordinate reference constructs
tas.set_construct(horizontal_crs)
tas.set_construct(vertical_crs)

# Create and set the cell measure constructs
cell_measure = cfdm.CellMeasure(
    measure="area",
    properties={"units": "km2"},
    data=cfdm.Data(numpy.arange(90.0).reshape(9, 10)),
)

tas.set_construct(cell_measure, axes=[axis_X, axis_Y])

print(tas)
import netCDF4

nc = netCDF4.Dataset("file.nc", "r")
v = nc.variables["ta"]
netcdf_array = cfdm.NetCDFArray(
    filename="file.nc",
    ncvar="ta",
    dtype=v.dtype,
    ndim=v.ndim,
    shape=v.shape,
    size=v.size,
)
data_disk = cfdm.Data(netcdf_array)
numpy_array = v[...]
data_memory = cfdm.Data(numpy_array)
data_disk.equals(data_memory)
key = tas.construct_key("surface_altitude")
orog = tas.convert(key)
print(orog)
orog1 = tas.convert(key, full_domain=False)
print(orog1)
cfdm.write(tas, "tas.nc")
f = cfdm.read("tas.nc")
f
fields = cfdm.read("tas.nc", extra="domain_ancillary")
fields
orog_from_file = fields[3]
print(orog_from_file)

print("\n**Copying and equality**\n")

u = t.copy()
u.data[0, 0, 0] = -1e30
u.data[0, 0, 0]
t.data[0, 0, 0]
key = u.construct_key("grid_latitude")
u.del_construct(key)
u.constructs("grid_latitude")
t.constructs("grid_latitude")
import copy

u = copy.deepcopy(t)
orog = t.constructs("surface_altitude").value().copy()
t.equals(t)
t.equals(t.copy())
t.equals(t[...])
t.equals(q)
t.equals(q, verbose=True)
cfdm.ATOL()
cfdm.RTOL()
original = cfdm.RTOL(0.00001)
cfdm.RTOL()
cfdm.RTOL(original)
cfdm.RTOL()
orog = t.constructs("surface_altitude").value()
orog.equals(orog.copy())

print("\n**NetCDF interface**\n")

print(t.constructs.filter_by_ncvar("b"))
t.constructs("ncvar%x").value()
t.constructs("ncdim%x")
q.nc_get_variable()
q.nc_global_attributes()
q.nc_set_variable("humidity")
q.nc_get_variable()
q.constructs("latitude").value().nc_get_variable()

print("\n**Writing to disk**\n")

print(q)
cfdm.write(q, "q_file.nc")
x
cfdm.write(x, "new_file.nc")
f = cfdm.read("q_file.nc")[0]
q.equals(f)
f.set_property("model", "model_A")
cfdm.write(f, "f_file.nc", global_attributes="model")
f.nc_global_attributes()
f.nc_set_global_attribute("model")
f.nc_global_attributes()
f.nc_global_attributes(values=True)
cfdm.write(f, "f_file.nc")
f.set_property("information", "variable information")
f.properties()
f.nc_set_global_attribute("information", "global information")
f.nc_global_attributes()
cfdm.write(f, "f_file.nc")
cfdm.write(f, "f_file_nc", file_descriptors={"history": "created in 2020"})
f_file = cfdm.read("f_file.nc")[0]
f_file.nc_global_attributes()
f_file.properties()
f_file.nc_global_attributes()
f_file.set_property("Conventions", "UGRID1.0")
cfdm.write(f, "f_file.nc", Conventions="UGRID1.0")
print(q)
key = q.construct_key("time")
axes = q.get_data_axes(key)
axes
q2 = q.insert_dimension(axis=axes[0])
q2
cfdm.write(q2, "q2_file.nc")

print("\n**Hierarchical groups**\n")


print("\n**External variables**\n")

u = cfdm.read("parent.nc")[0]
print(u)
area = u.constructs("measure:area").value()
area
area.nc_get_external()
area.nc_get_variable()
area.properties()
area.has_data()
g = cfdm.read("parent.nc", external="external.nc")[0]
print(g)
area = g.constructs("measure:area").value()
area
area.nc_get_external()
area.nc_get_variable()
area.properties()
area.data
area.nc_set_external(True)
cfdm.write(g, "new_parent.nc")
cfdm.write(g, "new_parent.nc", external="new_external.nc")

print("\n**Compression**\n")

h = cfdm.read("contiguous.nc")[0]
print(h)
print(h.data.array)
h.data.get_compression_type()
print(h.data.compressed_array)
count_variable = h.data.get_count()
count_variable
print(count_variable.data.array)
station2 = h[1]
station2
print(station2.data.array)
h.data.get_compression_type()
h.data[1, 2] = -9
print(h.data.array)
h.data.get_compression_type()

import numpy
import cfdm

# Define the array values
data = cfdm.Data(
    [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.5]],
    mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
)

# Create the field construct
T = cfdm.Field()
T.set_properties(
    {
        "standard_name": "air_temperature",
        "units": "K",
        "featureType": "timeSeries",
    }
)

# Create the domain axis constructs
X = T.set_construct(cfdm.DomainAxis(4))
Y = T.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
T.set_data(data, axes=[Y, X])

# Compress the data
T.compress(
    "contiguous",
    count_properties={"long_name": "number of obs for this timeseries"},
    inplace=True,
)

T
print(T.data.array)
T.data.get_compression_type()
print(T.data.compressed_array)
count_variable = T.data.get_count()
count_variable
print(count_variable.data.array)
cfdm.write(T, "T_contiguous.nc")

import numpy
import cfdm

# Define the ragged array values
ragged_array = cfdm.Data([280, 281, 279, 278, 279.5])

# Define the count array values
count_array = [1, 4]

# Create the count variable
count_variable = cfdm.Count(data=cfdm.Data(count_array))
count_variable.set_property("long_name", "number of obs for this timeseries")

# Create the contiguous ragged array object, specifying the
# uncompressed shape
array = cfdm.RaggedContiguousArray(
    compressed_array=ragged_array,
    shape=(2, 4),
    size=8,
    ndim=2,
    count_variable=count_variable,
)

# Create the field construct with the domain axes and the ragged
# array
T = cfdm.Field()
T.set_properties(
    {
        "standard_name": "air_temperature",
        "units": "K",
        "featureType": "timeSeries",
    }
)

# Create the domain axis constructs for the uncompressed array
X = T.set_construct(cfdm.DomainAxis(4))
Y = T.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
T.set_data(cfdm.Data(array), axes=[Y, X])

p = cfdm.read("gathered.nc")[0]
print(p)
print(p.data.array)
p.data.get_compression_type()
print(p.data.compressed_array)
list_variable = p.data.get_list()
list_variable
print(list_variable.data.array)
p[0]
p[1, :, 3:5]
p.data.get_compression_type()
p.data[1] = -9
p.data.get_compression_type()

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
    compressed_dimension=1,
    shape=(2, 3, 2),
    size=12,
    ndim=3,
    list_variable=list_variable,
)

# Create the field construct with the domain axes and the gathered
# array
P = cfdm.Field(
    properties={"standard_name": "precipitation_flux", "units": "kg m-2 s-1"}
)

# Create the domain axis constructs for the uncompressed array
T = P.set_construct(cfdm.DomainAxis(2))
Y = P.set_construct(cfdm.DomainAxis(3))
X = P.set_construct(cfdm.DomainAxis(2))

# Set the data for the field
P.set_data(cfdm.Data(array), axes=[T, Y, X])

P
print(P.data.array)
P.data.get_compression_type()
print(P.data.compressed_array)
list_variable = P.data.get_list()
list_variable
print(list_variable.data.array)
cfdm.write(P, "P_gathered.nc")
