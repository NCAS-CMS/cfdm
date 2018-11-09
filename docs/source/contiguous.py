import cfdm, numpy

f = cfdm.read('~/cfdm/test/DSG_timeSeries_contiguous.nc')[1]


f.get_construct('time').del_property('long_name')
f.get_construct('height').del_property('long_name')
f.get_construct('latitude').del_property('long_name')
f.get_construct('longitude').del_property('long_name')

f.del_construct('long_name:some kind of station info')

#array = f.get_array()
#print array.shape
#f.data[0, 0:3] = numpy.around(numpy.random.uniform(0.01, 0.2, 3),2)
#f.data[1, 0:7] = numpy.around(numpy.random.uniform(0.01, 0.2, 7),2)
#f.data[2, 0:6] = numpy.around(numpy.random.uniform(0.01, 0.2, 6),2)
#f.data[3, 0:9] = numpy.around(numpy.random.uniform(0.01, 0.2, 9),2)
#print (f.get_array())
print (f.get_array())

n = cfdm.NumpyArray(numpy.around(numpy.random.uniform(0.01, 0.2, 24),2))

f.data._get_Array()._set_compressed_Array(n)

f.get_array()
print (f.get_array())


cfdm.write(f, 'contiguous.nc', fmt='NETCDF3_CLASSIC')
