import numpy
import netCDF4

n = netCDF4.Dataset('gathered.nc', 'w', format='NETCDF3_CLASSIC')

n.Conventions = 'CF-1.7'

n.createDimension('time'   ,  2)
n.createDimension('lat'    ,  4)
n.createDimension('lon'    ,  5)

n.createDimension('landpoint',  7)
        
# Dimension coordinate variables
time = n.createVariable('time', 'f8', ('time',))
time.standard_name = "time"
time.units = "days since 2000-1-1"
time[...] = [31, 60]

lat = n.createVariable('lat', 'f8', ('lat',))
lat.standard_name = "latitude"
lat.units = "degrees_north"
lat[...] = [-90, -85, -80, -75]

lon = n.createVariable('lon', 'f8', ('lon',))
lon.standard_name = "longitude"
lon.units = "degrees_east"
lon[...] = [0, 10, 20, 30, 40]

landpoint = n.createVariable('landpoint', 'i', ('landpoint',))
landpoint.compress = "lat lon"
landpoint[...] = [1, 2, 5, 7, 8, 16, 18]

       
# Data variables
pr = n.createVariable('pr', 'f8', ('time', 'landpoint'))
pr.standard_name = "precipitation_flux"
pr.units = "kg m2 s-1"
pr[...] = [ 0.000122, 0.0008, 0.000177, 0.000175, 0.00058, 0.000206, 0.0007,
  0.000202, 0.000174, 0.00084, 0.000201, 0.0057, 0.000223, 0.000102 ]

n.close()
