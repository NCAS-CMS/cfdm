import netCDF4, numpy

n = netCDF4.Dataset('compressed_by_gathering.nc', 'w', format='NETCDF3_CLASSIC')

n.Conventions = 'CF-1.6'

time    = n.createDimension('time'   ,  2)
height  = n.createDimension('height' ,  3)
lat     = n.createDimension('lat'    ,  4)
lon     = n.createDimension('lon'    ,  5)
p       = n.createDimension('p'      ,  6)

list1  = n.createDimension('list1',  4)
list2  = n.createDimension('list2',  9)
list3  = n.createDimension('list3', 14)

# Dimension coordinate variables
time = n.createVariable('time', 'f8', ('time',))
time.standard_name = "time"
time.units = "days since 2000-1-1"
time.positive = "up"
time[...] = [31, 60]

height = n.createVariable('height', 'f8', ('height',))
height.standard_name = "height"
height.units = "metres"
height.positive = "up"
height[...] = [0.5, 1.5, 2.5]

lat = n.createVariable('lat', 'f8', ('lat',))
lat.standard_name = "latitude"
lat.units = "degrees_north"
lat[...] = [-90, -85, -80, -75]

p = n.createVariable('p', 'i4', ('p',))
p.long_name = "pseudolevel"
p[...] = [1, 2, 3, 4, 5, 6]

# Auxiliary coordinate variables

aux0 = n.createVariable('aux0', 'f8', ('list1',))
aux0.standard_name = "longitude"
aux0.units = "degrees_east"
aux0[...] = numpy.arange(list1.size)

aux1 = n.createVariable('aux1', 'f8', ('list3',))
aux1[...] = numpy.arange(list3.size)

aux2 = n.createVariable('aux2', 'f8', ('time', 'list3', 'p'))
aux2[...] = numpy.arange(time.size * list3.size * p.size)

aux3 = n.createVariable('aux3', 'f8', ('p', 'list3', 'time'))
aux3[...] = numpy.arange(p.size * list3.size * time.size)

aux4 = n.createVariable('aux4', 'f8', ('p', 'time', 'list3'))
aux4[...] = numpy.arange(p.size * time.size * list3.size)

aux5 = n.createVariable('aux5', 'f8', ('list3', 'p', 'time'))
aux5[...] = numpy.arange(list3.size * p.size * time.size)

aux6 = n.createVariable('aux6', 'f8', ('list3', 'time'))
aux6[...] = numpy.arange(list3.size * time.size)

aux7 = n.createVariable('aux7', 'f8', ('lat',))
aux7[...] = numpy.arange(lat.size)

aux8 = n.createVariable('aux8', 'f8', ('lon', 'lat',))
aux8[...] = numpy.arange(lon.size * lat.size)

aux9 = n.createVariable('aux9', 'f8', ('time', 'height'))
aux9[...] = numpy.arange(time.size * height.size)

# List variables
list1 = n.createVariable('list1', 'i', ('list1',))
list1.compress = "lon"
list1[...] = [0, 1, 3, 4]

list2 = n.createVariable('list2', 'i', ('list2',))
list2.compress = "lat lon"
list2[...] = [0,  1,  5,  6, 13, 14, 17, 18, 19]

list3 = n.createVariable('list3', 'i', ('list3',))
list3.compress = "height lat lon"
list3[...] = [0, 1, 5,  6, 13, 14, 25, 26, 37, 38, 48, 49, 58, 59]

# Data variables
temp1 = n.createVariable('temp1', 'f8', ('time', 'height', 'lat', 'list1', 'p'))
temp1.long_name = "temp1"
temp1.units = "K"
temp1.coordinates = "aux0 aux1 aux2 aux3 aux4 aux5 aux6 aux7 aux8 aux9"
temp1[...] = numpy.arange(2*3*4*4*6)

temp2 = n.createVariable('temp2', 'f8', ('time', 'height', 'list2', 'p'))
temp2.long_name = "temp2"
temp2.units = "K"
temp2.coordinates = "aux0 aux1 aux2 aux3 aux4 aux5 aux6 aux7 aux8 aux9"
temp2[...] = numpy.arange(2*3*9*6)

temp3 = n.createVariable('temp3', 'f8', ('time', 'list3', 'p'))
temp3.long_name = "temp3"
temp3.units = "K"
temp3.coordinates = "aux0 aux1 aux2 aux3 aux4 aux5 aux6 aux7 aux8 aux9"
temp3[...] = numpy.arange(2*14*6)

n.close()
