import cfdm, numpy

f = cfdm.read('~/cfdm/test/DSG_timeSeries_contiguous.nc')[1]


f.get_construct('time').del_property('long_name')
f.get_construct('height').del_property('long_name')
f.get_construct('latitude').del_property('long_name')
f.get_construct('longitude').del_property('long_name')

f.del_construct('long_name:some kind of station info')


cfdm.write(f, 'contiguous.nc', fmt='NETCDF3_CLASSIC')
