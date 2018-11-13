import cfdm
import numpy


f = cfdm.read('test/test_file.nc')[0]

f.set_property('standard_name', 'air_temperature')
f.set_property('units', 'K')
f.set_property(u'project', 'research')
f.set_property(u'Conventions', 'CF-1.7')

f.del_property('flag_masks')
f.del_property('flag_values')
f.del_property('flag_meanings')

f.data[0,...] = numpy.around(numpy.random.uniform(260, 280, 90), 1).reshape(10, 9)

f.nc_global_attributes(['project'])
f.nc_set_variable('ta')

lat = f.get_construct('grid_latitude')
data = numpy.array([  2.2, 1.76, 1.32, 0.88,  0.44,  0.0, -0.44,  -0.88,  -1.32, -1.76])
data = numpy.around(data, 2)
lat.set_data(cfdm.Data(data))
lat.nc_set_variable('lat')

bounds = numpy.empty((10, 2))
bounds[:, 0] = data + 0.22
bounds[:, 1] = data - 0.22
bounds = numpy.around(bounds, 2)
b = cfdm.Bounds()
b.set_data(cfdm.Data(bounds))
lat.set_bounds(b)
lat.bounds.nc_set_variable('lat_bnds')

lon = f.get_construct('grid_longitude')
data = numpy.array([-4.7, -4.26, -3.820, -3.38, -2.94, -2.5, -2.06, -1.620, -1.18])
data = numpy.around(data, 2)
lon.set_data(cfdm.Data(data))
lon.nc_set_variable('lon')

bounds = numpy.empty((9, 2))
bounds[:, 0] = data - 0.22
bounds[:, 1] = data + 0.22
bounds = numpy.around(bounds, 2)
lon.get_bounds().set_data(cfdm.Data(bounds))
lon.bounds.nc_set_variable('lon_bnds')

lat = f.get_construct('latitude')
data = numpy.array([[ 53.941,  53.987,  54.029,  54.066,  54.099,  54.127,  54.15 ,
         54.169,  54.184],
       [ 53.504,  53.55 ,  53.591,  53.627,  53.66 ,  53.687,  53.711,
         53.729,  53.744],
       [ 53.067,  53.112,  53.152,  53.189,  53.221,  53.248,  53.271,
         53.29 ,  53.304],
       [ 52.629,  52.674,  52.714,  52.75 ,  52.782,  52.809,  52.832,
         52.85 ,  52.864],
       [ 52.192,  52.236,  52.276,  52.311,  52.343,  52.37 ,  52.392,
         52.41 ,  52.424],
       [ 51.754,  51.798,  51.837,  51.873,  51.904,  51.93 ,  51.953,
         51.971,  51.984],
       [ 51.316,  51.36 ,  51.399,  51.434,  51.465,  51.491,  51.513,
         51.531,  51.545],
       [ 50.879,  50.922,  50.96 ,  50.995,  51.025,  51.052,  51.074,
         51.091,  51.105],
       [ 50.441,  50.484,  50.522,  50.556,  50.586,  50.612,  50.634,
         50.652,  50.665],
       [ 50.003,  50.045,  50.083,  50.117,  50.147,  50.173,  50.194,
         50.212,  50.225]])
data = numpy.around(data, 3)
lat.set_data(cfdm.Data(data))
lat.set_property('units', 'degrees_N')

lon = f.get_construct('longitude')
data = numpy.array([[ 2.004,  2.747,  3.492,  4.238,  4.986,  5.734,  6.484,  7.234,
         7.985],
       [ 2.085,  2.821,  3.558,  4.297,  5.037,  5.778,  6.52 ,  7.262,
         8.005],
       [ 2.165,  2.893,  3.623,  4.355,  5.087,  5.821,  6.555,  7.29 ,
         8.026],
       [ 2.243,  2.964,  3.687,  4.411,  5.136,  5.862,  6.589,  7.317,
         8.045],
       [ 2.319,  3.033,  3.749,  4.466,  5.184,  5.903,  6.623,  7.344,
         8.065],
       [ 2.394,  3.101,  3.81 ,  4.52 ,  5.231,  5.944,  6.656,  7.37 ,
         8.084],
       [ 2.467,  3.168,  3.87 ,  4.573,  5.278,  5.983,  6.689,  7.395,
         8.102],
       [ 2.539,  3.233,  3.929,  4.626,  5.323,  6.022,  6.721,  7.42 ,
         8.121],
       [ 2.61 ,  3.298,  3.987,  4.677,  5.368,  6.059,  6.752,  7.445,
         8.139],
       [ 2.679,  3.361,  4.043,  4.727,  5.411,  6.097,  6.783,  7.469,
         8.156]])
data = numpy.around(data, 3)
lon.set_data(cfdm.Data(data))
lon.set_property('units', 'degrees_E')

area = f.get_construct('measure%area')
data = numpy.array([[ 2391.9657,  2391.9657,  2391.9657,  2391.9657,  2391.9657,
                      2391.9657,  2391.9657,  2391.9657,  2391.9657],
                    [ 2392.6009,  2392.6009,  2392.6009,  2392.6009,  2392.6009,
                      2392.6009,  2392.6009,  2392.6009,  2392.6009],
                    [ 2393.0949,  2393.0949,  2393.0949,  2393.0949,  2393.0949,
                      2393.0949,  2393.0949,  2393.0949,  2393.0949],
                    [ 2393.4478,  2393.4478,  2393.4478,  2393.4478,  2393.4478,
                      2393.4478,  2393.4478,  2393.4478,  2393.4478],
                    [ 2393.6595,  2393.6595,  2393.6595,  2393.6595,  2393.6595,
                      2393.6595,  2393.6595,  2393.6595,  2393.6595],
                    [ 2393.7301,  2393.7301,  2393.7301,  2393.7301,  2393.7301,
                      2393.7301,  2393.7301,  2393.7301,  2393.7301],
                    [ 2393.6595,  2393.6595,  2393.6595,  2393.6595,  2393.6595,
                      2393.6595,  2393.6595,  2393.6595,  2393.6595],
                    [ 2393.4478,  2393.4478,  2393.4478,  2393.4478,  2393.4478,
                      2393.4478,  2393.4478,  2393.4478,  2393.4478],
                    [ 2393.0949,  2393.0949,  2393.0949,  2393.0949,  2393.0949,
                      2393.0949,  2393.0949,  2393.0949,  2393.0949],
                    [ 2392.6009,  2392.6009,  2392.6009,  2392.6009,  2392.6009,
                      2392.6009,  2392.6009,  2392.6009,  2392.6009]])
data = numpy.around(data, 4)
area.set_data(cfdm.Data(data))

orog = f.get_construct('surface_altitude').data[-1, -1] = 79.8


t = cfdm.DimensionCoordinate(properties={'standard_name': 'time',
                                         'units': 'days since 2018-12-01'})
t.set_data(cfdm.Data([31.0]))

a=cfdm.FieldAncillary(properties={'standard_name': 'air_temperature standard_error',
                                  'units': 'K'})
data = numpy.random.uniform(0.1, 0.9, 90).reshape(10, 9)
data = numpy.around(data, 2)
a.set_data(cfdm.Data(data))

tda = f.set_domain_axis(cfdm.DomainAxis(1))

f.set_dimension_coordinate(t, axes=[tda])
f.set_field_ancillary(a, axes=['domainaxis1', 'domainaxis2'])

f.del_construct('ncvar%ancillary_data')
f.del_construct('ncvar%ancillary_data_1')
f.del_construct('ncvar%ancillary_data_2')

f.get_construct('long_name:greek_letters').set_property('long_name', 'Grid latitude name')

f.cell_methods()['cellmethod0'].del_property('comment')
f.cell_methods()['cellmethod0'].set_property('intervals', [cfdm.Data(0.1 , 'degrees')])
f.cell_methods()['cellmethod0'].set_property('where', 'land')
f.cell_methods()['cellmethod0'].set_axes(['domainaxis1', 'domainaxis2'])

f.cell_methods()['cellmethod1'].set_property('method', 'maximum')
f.cell_methods()['cellmethod1'].del_property('where')
f.cell_methods()['cellmethod1'].set_axes([tda])


f.dump()

print(f)



h = cfdm.Field()
h.properties({'standard_name': 'specific_humidity',
              'units': '1',
              'project': 'research',
              })
h.nc_global_attributes(['project'])
h.nc_set_variable('q')

y = h.set_domain_axis(cfdm.DomainAxis(5))
x = h.set_domain_axis(cfdm.DomainAxis(8))
t = h.set_domain_axis(cfdm.DomainAxis(1))

data = numpy.random.uniform(0, 0.15, 40).reshape(5, 8)
data[[1, 3]] /= 2.
data[[0, 4]] /= 4.
data = numpy.around(data, 3)
h.set_data(cfdm.Data(data), axes=[y, x])

lat = cfdm.DimensionCoordinate(properties={'standard_name': 'latitude',
                                           'units': 'degrees_north'})
data = numpy.array([-75, -45, 0, 45, 75.])
data = numpy.around(data, 1)
lat.set_data(cfdm.Data(data))

bounds = numpy.empty((5, 2))
bounds[:, 0] = [-90, -60, -30, 30, 60]
bounds[:, 1] = [-60, -30, 30, 60, 90]
bounds = numpy.around(bounds, 1)
b = cfdm.Bounds()
b.set_data(cfdm.Data(bounds))
lat.set_bounds(b)

lon = cfdm.DimensionCoordinate(properties={'standard_name': 'longitude',
                                           'units': 'degrees_east'})
data = numpy.array([0, 45, 90, 135, 180, 225, 270., 315]) + 45/2.
data = numpy.around(data, 1)
lon.set_data(cfdm.Data(data))

bounds = numpy.empty((8, 2))
bounds[:, 0] = data - 45/2.
bounds[:, 1] = data + 45/2.
bounds = numpy.around(bounds, 1)
b = cfdm.Bounds()
b.set_data(cfdm.Data(bounds))
lon.set_bounds(b)


time = cfdm.DimensionCoordinate(properties={'standard_name': 'time',
                                            'units': 'days since 2018-12-01'})
time.set_data(cfdm.Data([31.0]))

cell_method = cfdm.CellMethod(axes=['area'], properties={'method': 'mean'})

h.set_dimension_coordinate(lat , axes=[y])
h.set_dimension_coordinate(lon , axes=[x])
h.set_dimension_coordinate(time, axes=[t])

h.set_cell_method(cell_method)

print h.constructs()
h.dump()
print h


cfdm.write([h, f], 'file.nc', fmt='NETCDF3_CLASSIC')

#cfdm.write(f, 'file.nc', fmt='NETCDF3_CLASSIC')


