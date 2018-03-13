import netCDF4
import numpy

nc = netCDF4.Dataset('test/bad_file.nc', 'w', format='NETCDF3_CLASSIC')

nc.Conventions = 'CF-1.7'

time    = nc.createDimension('time'   ,  2)
height  = nc.createDimension('height' ,  3)
lat     = nc.createDimension('lat'    ,  4)
lon     = nc.createDimension('lon'    ,  5)
p       = nc.createDimension('p'      ,  6)
bounds2 = nc.createDimension('bounds2',  2)

# Dimension coordinate variables
time = nc.createVariable('time', 'f8', ('time',))
time.standard_name = "time"
time.units = "days since 2000-1-1"
time.bounds = 'time_bounds'
time[...] = numpy.arange(time.size)

height = nc.createVariable('height', 'f8', ('height',))
height.standard_name = "height"
height.units = "metres"
height.positive = "up"
height.bounds = 'height_bounds'
height[...] = numpy.arange(height.size)

nc.createVariable('height_bounds', 'f8', ('time', 'bounds2'))

lat = nc.createVariable('lat', 'f8', ('lat',))
lat.standard_name = 'latitude'
lat.units = "degrees_east"
lat.bounds = 'lat_bounds'
lat[...] = numpy.arange(lat.size)

nc.createVariable('lat_bounds', 'f8', ('lat',))

lon = nc.createVariable('lon', 'f8', ('lon',))
lon.standard_name = 'longitude'
lon.units = "degrees_north"
lon.bounds = 'lon_bounds'
lon[...] = numpy.arange(lon.size)

nc.createVariable('lon_bounds', 'f8', ())

eastward_wind = nc.createVariable('eastward_wind', 'f8', ('time', 'height', 'lat', 'lon'))
eastward_wind.coordinates = 'var1'
eastward_wind[...] = numpy.arange(eastward_wind.size)

nc.close()
