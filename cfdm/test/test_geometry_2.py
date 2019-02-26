from __future__ import print_function
import datetime
import os
import tempfile
import unittest

import numpy
import netCDF4

import cfdm

def _make_interior_ring_file(filename):        
    n = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    
    # Global arttributes
    n.Conventions = 'CF-1.8'
    n.featureType = 'timeSeries'

    # Dimensions
    time     = n.createDimension('time', 4)
    instance = n.createDimension('instance', 2)
    node     = n.createDimension('node', 12)
    part     = n.createDimension('part', 4)

    # Variables
    t = n.createVariable('time', 'i4', ('time',))
    t.standard_name = "time" 
    t.units = "days since 2000-01-01"
    t[...] = [1, 2, 3, 4]

    x = n.createVariable('x', 'f8', ('node',))
    x.units = "degrees_east"
    x.standard_name = "longitude"
    x.axis = "X"
    x[...] = [20, 10, 0, 5, 10, 15, 20, 10, 0, 50, 40, 30]
 
    y = n.createVariable('y', 'f8', ('node',))
    y.units = "degrees_north"
    y.standard_name = "longitude"
    y.axis = "Y"
    y[...] = [0, 15, 0, 5, 10, 5, 20, 35, 20, 0, 15, 0]
 
    lat = n.createVariable('lat', 'f8', ('instance',))
    lat.units = "degrees_north" 
    lat.standard_name = "latitude"
    lat.bounds = "y"
    lat[...] = [25, 7]

    lon = n.createVariable('lon', 'f8', ('instance',))
    lon.units = "degrees_east"
    lon.standard_name = "longitude"
    lon.bounds = "x"
    lon[...] = [10, 40]

    geometry_container = n.createVariable('geometry_container', 'i4', ())
    geometry_container.geometry_type = "polygon"
    geometry_container.node_count = "node_count"
    geometry_container.node_coordinates = "x y"
    geometry_container.grid_mapping = "datum"
    geometry_container.coordinates = "lat lon"
    geometry_container.part_node_count = "part_node_count"
    geometry_container.interior_ring = "interior_ring"

    node_count = n.createVariable('node_count', 'i4', ('instance'))
    node_count[...] = [9, 3]

    part_node_count = n.createVariable('part_node_count', 'i4', ('part'))
    part_node_count[...] = [3, 3, 3, 3]
    
    interior_ring = n.createVariable('interior_ring', 'i4', ('part'))
    interior_ring[...] = [0, 1, 0, 0]

    datum = n.createVariable('datum', 'f4', ())
    datum.grid_mapping_name = "latitude_longitude"
    datum.semi_major_axis = 6378137.
    datum.inverse_flattening = 298.257223563
    datum.longitude_of_prime_meridian = 0.
    
    someData = n.createVariable('someData', 'f8', ('instance', 'time'))
    someData.coordinates = "time lat lon"
    someData.grid_mapping = "datum"
    someData.geometry = "geometry_container"
    someData[...]= [1, 2, 3, 4,
                    5, 6, 7, 8]
  
    n.close()
    
    return filename
#--- End: def

interior_ring_file = _make_interior_ring_file('geometry_interior_ring.nc')

class DSGTest(unittest.TestCase):
    def setUp(self):
        self.geometry_interior_ring_file = interior_ring_file

        (fd, self.tempfilename) = tempfile.mkstemp(suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)
        
        self.test_only = []
    #--- End: def
 
    def tearDown(self):
        os.remove(self.tempfilename)
    #--- End: def
    
    def test_geometry_2(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.geometry_interior_ring_file, verbose=True)

        for i in f:
            i.dump()
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
    
