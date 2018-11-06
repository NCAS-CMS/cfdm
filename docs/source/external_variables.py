import cfdm

f = cfdm.read('parent.nc')[0]
print(f)
c = f.get_construct('measure%area')
print(repr(c))
print(c.nc_get_external())
print(c.nc_get_variable())
print(c.properties())
print(c.has_data())

g = cfdm.read('parent.nc', external_files='external.nc')[0]
print(g)
c = g.get_construct('measure%area')
print(repr(c))
print(c.nc_get_external())
print(c.nc_get_variable())
print(c.properties())
print(c.get_data())

print(c.nc_set_external(True))
cfdm.write(g, 'new_parent.nc', external_file='new_external.nc')
