import netCDF4
import numpy

nc = netCDF4.Dataset('test/bad_file.nc', 'w', format='NETCDF3_CLASSIC')

nc.Conventions = 'CF-1.7'

time    = nc.createDimension('time'   ,  2)
z       = nc.createDimension('z'      ,  3)
#z2      = nc.createDimension('z2'     ,  3)
lat     = nc.createDimension('lat'    ,  4)
lon     = nc.createDimension('lon'    ,  5)
p       = nc.createDimension('p'      ,  6)
bounds2 = nc.createDimension('bounds2',  2)

# Dimension coordinate variables
time = nc.createVariable('time', 'f8', ('time',))
time.standard_name = "time"
time.units = "days since 2000-1-1"
time.bounds = 'time_bounds' # Bounds variable is not in file
time[...] = numpy.arange(time.size)

z = nc.createVariable('z', 'f8', ('z',))
z.standard_name = "atmosphere_sigma_coordinate"
z.units = "metres"
z.positive = "up"
z.bounds = 'z_bounds'
z.formula_terms = "sigma: z ps: ps ptop: ptop"
z[...] = numpy.arange(z.size)

nc.createVariable('z_bounds', 'f8', ('time', 'bounds2')) #  Bounds span incorrect dimensions

nc.createVariable('ps', 'f8', ('time', 'bounds2')) #  Bounds span incorrect dimensions

nc.createVariable('ptop', 'f8', ('lon', 'lat'))

lat = nc.createVariable('lat', 'f8', ('lat',))
lat.standard_name = 'latitude'
lat.units = "degrees_east"
lat.bounds = 'lat_bounds'
lat[...] = numpy.arange(lat.size)

nc.createVariable('lat_bounds', 'f8', ('lat',)) # Bounds span incorrect dimensions

lon = nc.createVariable('lon', 'f8', ('lon',))
lon.standard_name = 'longitude'
lon.units = "degrees_north"
lon.bounds = 'lon_bounds'
lon[...] = numpy.arange(lon.size)

nc.createVariable('lon_bounds', 'f8', ())  # Bounds span incorrect dimensions

eastward_wind = nc.createVariable('eastward_wind', 'f8', ('time', 'z', 'lat', 'lon'))
eastward_wind.coordinates = 'var1' # Auxiliary/scalar coordinate variable is not in file
eastward_wind[...] = numpy.arange(eastward_wind.size)

nc.close()
