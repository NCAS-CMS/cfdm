from __future__ import print_function
import datetime
import inspect
import os
import tempfile
import unittest

import numpy
import netCDF4

import cfdm

def _make_geometry_1_file(filename):
    '''See n.comment for details.

    '''
    n = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    
    n.Conventions = 'CF-1.8'
    n.featureType = 'timeSeries'
    n.comment     = "Make a netCDF file with 2 node coordinates variables, each of which has a corresponding auxiliary coordinate variable."
    
    time     = n.createDimension('time'    , 4)
    instance = n.createDimension('instance', 2)
    node     = n.createDimension('node'    , 5)
    
    t =  n.createVariable('time', 'i4', ('time',))
    t.units = "seconds since 2016-11-07 20:00 UTC" 
    t[...] = [1, 2, 3, 4 ]

    lat = n.createVariable('lat', 'f8', ('instance',))
    lat.standard_name = "latitude"
    lat.units = "degrees_north"
    lat.nodes = "y"
    lat[...] = [30, 50]

    lon = n.createVariable('lon', 'f8', ('instance',))
    lon.standard_name = "longitude"
    lon.units = "degrees_east"
    lon.nodes = "x"
    lon[...] = [10, 60]    

    datum = n.createVariable('datum', 'i4', ())
    datum.grid_mapping_name = "latitude_longitude"
    datum.longitude_of_prime_meridian = 0.0
    datum.semi_major_axis = 6378137.0
    datum.inverse_flattening = 298.257223563
    
    geometry_container = n.createVariable('geometry_container', 'i4', ());
    geometry_container.geometry_type = "line"
    geometry_container.node_count = "node_count"
    geometry_container.node_coordinates = "x y"
    geometry_container.geometry_dimension = "instance"
    
    node_count = n.createVariable('node_count', 'i4', ('instance',))
    node_count[...] = [3, 2]
    
    x = n.createVariable('x', 'f8', ('node',))
    x.units = "degrees_east"
    x.standard_name = "longitude"
    x.axis = "X"
    x[...] = [30, 10, 40, 50, 50]
    
    y = n.createVariable('y', 'f8', ('node',))
    y.units = "degrees_north"
    y.standard_name = "latitude"
    y.axis = "Y"
    y[...] = [10, 30, 40, 60, 50]
    
    someData_1 = n.createVariable('someData_1', 'f8', ('instance', 'time'))
    someData_1.coordinates = "time lat lon"
    someData_1.grid_mapping = "datum"
    someData_1.geometry = "geometry_container"
    someData_1[...] = [[1, 2, 3, 4],
                       [5, 6, 7, 8]]

    someData_2 = n.createVariable('someData_2', 'f8', ('instance', 'time'))
    someData_2.coordinates = "time lat lon"
    someData_2.grid_mapping = "datum"
    someData_2.geometry = "geometry_container"
    someData_2[...] = [[10, 20, 30, 40],
                       [50, 60, 70, 80]]

    n.close()
    
    return filename
#--- End: def

def _make_geometry_2_file(filename):        
    '''See n.comment for details

    '''
    n = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    
    n.Conventions = 'CF-1.8'
    n.featureType = 'timeSeries'
    n.comment     = 'A netCDF file with 3 node coordinates variables, only two of which have a corresponding auxiliary coordinate variable.'
   
    time     = n.createDimension('time'    , 4)
    instance = n.createDimension('instance', 2)
    node     = n.createDimension('node'    , 5)
    
    t =  n.createVariable('time', 'i4', ('time',))
    t.units = "seconds since 2016-11-07 20:00 UTC" 
    t[...] = [1, 2, 3, 4 ]

    lat = n.createVariable('lat', 'f8', ('instance',))
    lat.standard_name = "latitude"
    lat.units = "degrees_north"
    lat.nodes = "y"
    lat[...] = [30, 50]

    lon = n.createVariable('lon', 'f8', ('instance',))
    lon.standard_name = "longitude"
    lon.units = "degrees_east"
    lon.nodes = "x"
    lon[...] = [10, 60]    

    datum = n.createVariable('datum', 'i4', ())
    datum.grid_mapping_name = "latitude_longitude"
    datum.longitude_of_prime_meridian = 0.0
    datum.semi_major_axis = 6378137.0
    datum.inverse_flattening = 298.257223563
    
    geometry_container = n.createVariable('geometry_container', 'i4', ());
    geometry_container.geometry_type = "line"
    geometry_container.node_count = "node_count"
    geometry_container.node_coordinates = "x y z"
    geometry_container.geometry_dimension = "instance"
    
    node_count = n.createVariable('node_count', 'i4', ('instance',))
    node_count[...] = [3, 2]
    
    x = n.createVariable('x', 'f8', ('node',))
    x.units = "degrees_east"
    x.standard_name = "longitude"
    x.axis = "X"
    x[...] = [30, 10, 40, 50, 50]
    
    y = n.createVariable('y', 'f8', ('node',))
    y.units = "degrees_north"
    y.standard_name = "latitude"
    y.axis = "Y"
    y[...] = [10, 30, 40, 60, 50]
    
    z = n.createVariable('z', 'f8', ('node',))
    z.units = "m"
    z.standard_name = "altitude"
    z.axis = "Z"
    z[...] = [100, 150, 200, 125, 80]
    
    someData = n.createVariable('someData', 'f8', ('instance', 'time'))
    someData.coordinates = "time lat lon"
    someData.grid_mapping = "datum"
    someData.geometry = "geometry_container"
    someData[...] = [[1, 2, 3, 4],
                     [5, 6, 7, 8]]

    someData_2 = n.createVariable('someData_2', 'f8', ('instance', 'time'))
    someData_2.coordinates = "time lat lon"
    someData_2.grid_mapping = "datum"
    someData_2.geometry = "geometry_container"
    someData_2[...] = [[1, 2, 3, 4],
                       [5, 6, 7, 8]]

    n.close()
    
    return filename
#--- End: def

def _make_geometry_3_file(filename):        
    '''See n.comment for details

    '''
    n = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    
    n.Conventions = 'CF-1.8'
    n.featureType = 'timeSeries'
    n.comment     = "A netCDF file with 3 node coordinates variables, each of which contains only one point, only two of which have a corresponding auxiliary coordinate variables. There is no node count variable."

   
    time     = n.createDimension('time'    , 4)
    instance = n.createDimension('instance', 3)
    node     = n.createDimension('node'    , 3)
    
    t =  n.createVariable('time', 'i4', ('time',))
    t.units = "seconds since 2016-11-07 20:00 UTC" 
    t[...] = [1, 2, 3, 4 ]

    lat = n.createVariable('lat', 'f8', ('instance',))
    lat.standard_name = "latitude"
    lat.units = "degrees_north"
    lat.nodes = "y"
    lat[...] = [30, 50, 70]
    
    lon = n.createVariable('lon', 'f8', ('instance',))
    lon.standard_name = "longitude"
    lon.units = "degrees_east"
    lon.nodes = "x"
    lon[...] = [10, 60, 80]    
    
    datum = n.createVariable('datum', 'i4', ())
    datum.grid_mapping_name = "latitude_longitude"
    datum.longitude_of_prime_meridian = 0.0
    datum.semi_major_axis = 6378137.0
    datum.inverse_flattening = 298.257223563
    
    geometry_container = n.createVariable('geometry_container', 'i4', ());
    geometry_container.geometry_type = "point"
    geometry_container.node_coordinates = "x y z"
    geometry_container.geometry_dimension = "instance"
    
    x = n.createVariable('x', 'f8', ('node',))
    x.units = "degrees_east"
    x.standard_name = "longitude"
    x.axis = "X"
    x[...] = [30, 10, 40]
    
    y = n.createVariable('y', 'f8', ('node',))
    y.units = "degrees_north"
    y.standard_name = "latitude"
    y.axis = "Y"
    y[...] = [10, 30, 40]
    
    z = n.createVariable('z', 'f8', ('node',))
    z.units = "m"
    z.standard_name = "altitude"
    z.axis = "Z"
    z[...] = [100, 150, 200]
    
    someData_1 = n.createVariable('someData_1', 'f8', ('instance', 'time'))
    someData_1.coordinates = "lat lon"
    someData_1.grid_mapping = "datum"
    someData_1.geometry = "geometry_container"
    someData_1[...] = [[1,  2,  3,  4],
                       [5,  6,  7,  8],
                       [9, 10, 11, 12]]
    
    someData_2 = n.createVariable('someData_2', 'f8', ('instance', 'time'))
    someData_2.coordinates = "lat lon"
    someData_2.grid_mapping = "datum"
    someData_2.geometry = "geometry_container"
    someData_2[...] = [[10,  20,  30,  40],
                       [50,  60,  70,  80],
                       [90, 100, 110, 120]]
    
    n.close()
    
    return filename
#--- End: def

def _make_geometry_4_file(filename):
    '''See n.comment for details.
    '''
    n = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
    
    n.Conventions = 'CF-1.8'
    n.featureType = 'timeSeries'
    n.comment     = "A netCDF file with 2 node coordinates variables, none of which have a corresponding auxiliary coordinate variable."
    
    time     = n.createDimension('time'    , 4)
    instance = n.createDimension('instance', 2)
    node     = n.createDimension('node'    , 5)
    strlen   = n.createDimension('strlen'  , 2)

    # Variables
    t = n.createVariable('time', 'i4', ('time',))
    t.standard_name = "time" 
    t.units = "days since 2000-01-01"
    t[...] = [1, 2, 3, 4]

    instance_id = n.createVariable('instance_id', 'S1', ('instance', 'strlen'))
    instance_id.cf_role = "timeseries_id"
    instance_id[...] = [['x', '1'],
                        ['y', '2']]

    datum = n.createVariable('datum', 'i4', ())
    datum.grid_mapping_name = "latitude_longitude"
    datum.longitude_of_prime_meridian = 0.0
    datum.semi_major_axis = 6378137.0
    datum.inverse_flattening = 298.257223563
    
    geometry_container = n.createVariable('geometry_container', 'i4', ());
    geometry_container.geometry_type = "line"
    geometry_container.node_count = "node_count"
    geometry_container.node_coordinates = "x y"
    geometry_container.geometry_dimension = "instance"
    
    node_count = n.createVariable('node_count', 'i4', ('instance',))
    node_count[...] = [3, 2]
    
    x = n.createVariable('x', 'f8', ('node',))
    x.units = "degrees_east"
    x.standard_name = "longitude"
    x.axis = "X"
    x[...] = [30, 10, 40, 50, 50]
    
    y = n.createVariable('y', 'f8', ('node',))
    y.units = "degrees_north"
    y.standard_name = "latitude"
    y.axis = "Y"
    y[...] = [10, 30, 40, 60, 50]
    
    someData_1 = n.createVariable('someData_1', 'f8', ('instance', 'time'))
    someData_1.coordinates = "instance_id"
    someData_1.grid_mapping = "datum"
    someData_1.geometry = "geometry_container"
    someData_1[...] = [[1, 2, 3, 4],
                       [5, 6, 7, 8]]

    someData_2 = n.createVariable('someData_2', 'f8', ('instance', 'time'))
    someData_2.coordinates = "instance_id"
    someData_2.grid_mapping = "datum"
    someData_2.geometry = "geometry_container"
    someData_2[...] = [[10, 20, 30, 40],
                       [50, 60, 70, 80]]

    n.close()
    
    return filename
#--- End: def

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
    strlen   = n.createDimension('strlen', 2)

    # Variables
    t = n.createVariable('time', 'i4', ('time',))
    t.standard_name = "time" 
    t.units = "days since 2000-01-01"
    t[...] = [1, 2, 3, 4]

    instance_id = n.createVariable('instance_id', 'S1', ('instance', 'strlen'))
    instance_id.cf_role = "timeseries_id"
    instance_id[...] = [['x', '1'],
                        ['y', '2']]
    
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
 
    z = n.createVariable('z', 'f8', ('node',))
    z.units = "m"
    z.standard_name = "altitude"
    z.axis = "Z"
    z[...] = [1, 2, 4, 2, 3, 4, 5, 1, 4, 3, 2, 1]
 
    lat = n.createVariable('lat', 'f8', ('instance',))
    lat.units = "degrees_north" 
    lat.standard_name = "latitude"
    lat.nodes = "y"
    lat[...] = [25, 7]

    lon = n.createVariable('lon', 'f8', ('instance',))
    lon.units = "degrees_east"
    lon.standard_name = "longitude"
    lon.nodes = "x"
    lon[...] = [10, 40]

    geometry_container = n.createVariable('geometry_container', 'i4', ())
    geometry_container.geometry_type = "polygon"
    geometry_container.node_count = "node_count"
    geometry_container.node_coordinates = "x y z"
    geometry_container.grid_mapping = "datum"
    geometry_container.coordinates = "lat lon"
    geometry_container.part_node_count = "part_node_count"
    geometry_container.interior_ring = "interior_ring"
    geometry_container.geometry_dimension = "instance"
    
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
    someData.coordinates = "time lat lon instance_id"
    someData.grid_mapping = "datum"
    someData.geometry = "geometry_container"
    someData[...]= [[1, 2, 3, 4],
                    [5, 6, 7, 8]]
  
    someData_2 = n.createVariable('someData_2', 'f8', ('instance', 'time'))
    someData_2.coordinates = "time lat lon instance_id"
    someData_2.grid_mapping = "datum"
    someData_2.geometry = "geometry_container"
    someData_2[...]= [[1, 2, 3, 4],
                      [5, 6, 7, 8]]
  
    n.close()
    
    return filename
#--- End: def

geometry_1_file    = _make_geometry_1_file('geometry_1.nc')
geometry_2_file    = _make_geometry_2_file('geometry_2.nc')
geometry_3_file    = _make_geometry_3_file('geometry_3.nc')
geometry_4_file    = _make_geometry_4_file('geometry_4.nc')
interior_ring_file = _make_interior_ring_file('geometry_interior_ring.nc')

class DSGTest(unittest.TestCase):
    def setUp(self):
        self.geometry_1_file = geometry_1_file
        self.geometry_2_file = geometry_2_file
        self.geometry_3_file = geometry_3_file
        self.geometry_4_file = geometry_4_file
        self.geometry_interior_ring_file = interior_ring_file

        (fd, self.tempfilename) = tempfile.mkstemp(suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)
        
        self.test_only = []
#        self.test_only = ['test_geometry_1']
#        self.test_only = ['test_geometry_3']

    #--- End: def
 
    def tearDown(self):
        os.remove(self.tempfilename)
    #--- End: def
    
    def test_geometry_1(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
                
        f = cfdm.read(self.geometry_1_file, verbose=False)

        self.assertTrue(len(f) == 2, 'f = '+repr(f))

        for g in f:
            self.assertTrue(g.equals(g.copy(), verbose=True))
            self.assertTrue(len(g.auxiliary_coordinates) == 2)
#            g.dump()
        
        g = f[0]
        for axis in ('X', 'Y'):
            coord = g.construct('axis='+axis)
            self.assertTrue( coord.has_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_part_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_interior_ring(), 'axis='+axis)

        cfdm.write(f, self.tempfilename, Conventions='CF-1.8', verbose=False)

        f2 = cfdm.read(self.tempfilename, verbose=False)

        self.assertTrue(len(f2) == 2, 'f2 = '+repr(f2))
        
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b, verbose=True))
    #--- End: def

    def test_geometry_2(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
                
        f = cfdm.read(self.geometry_2_file, verbose=False)

        self.assertTrue(len(f) == 2, 'f = '+repr(f))

        for g in f:
            self.assertTrue(g.equals(g.copy(), verbose=True))
            self.assertTrue(len(g.auxiliary_coordinates) == 3)
            #            g.dump()

        g = f[0]
        for axis in ('X', 'Y', 'Z'):
            coord = g.construct('axis='+axis)
            self.assertTrue( coord.has_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_part_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_interior_ring(), 'axis='+axis)

        cfdm.write(f, self.tempfilename, Conventions='CF-1.8', verbose=False)
#        cfdm.write(f, 'delme.nc', Conventions='CF-1.8', verbose=False)

        f2 = cfdm.read(self.tempfilename, verbose=False)

        self.assertTrue(len(f2) == 2, 'f2 = '+repr(f2))
        
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b, verbose=True))
    #--- End: def

    def test_geometry_3(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
                
        f = cfdm.read(self.geometry_3_file, verbose=False)

        self.assertTrue(len(f) == 2, 'f = '+repr(f))

        for g in f:
            self.assertTrue(g.equals(g.copy(), verbose=True))
            self.assertTrue(len(g.auxiliary_coordinates) == 3)
#            g.dump()

        g = f[0]
        for axis in ('X', 'Y', 'Z'):
            coord = g.construct('axis='+axis)
            self.assertFalse(coord.has_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_part_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_interior_ring(), 'axis='+axis)

        cfdm.write(f, self.tempfilename, Conventions='CF-1.8', verbose=False)
#        cfdm.write(f, 'delme.nc', Conventions='CF-1.8', verbose=False)

        f2 = cfdm.read(self.tempfilename, verbose=False)

        self.assertTrue(len(f2) == 2, 'f2 = '+repr(f2))
        
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b, verbose=True))
    #--- End: def

    def test_geometry_4(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
                
        f = cfdm.read(self.geometry_4_file, verbose=False)

        self.assertTrue(len(f) == 2, 'f = '+repr(f))

        for g in f:
            self.assertTrue(g.equals(g.copy(), verbose=True))
            self.assertTrue(len(g.auxiliary_coordinates) == 3)
#            g.dump()

        for axis in ('X', 'Y'):
            coord = g.construct('axis='+axis)
            self.assertTrue( coord.has_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_part_node_count(), 'axis='+axis)
            self.assertFalse(coord.has_interior_ring(), 'axis='+axis)

        cfdm.write(f, self.tempfilename, Conventions='CF-1.8', verbose=False)
#        cfdm.write(f, 'delme.nc', Conventions='CF-1.8', verbose=False)

        f2 = cfdm.read(self.tempfilename, verbose=False)

        self.assertTrue(len(f2) == 2, 'f2 = '+repr(f2))
        
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b, verbose=True))
    #--- End: def

    def test_geometry_interior_ring(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.geometry_interior_ring_file, verbose=False)

        self.assertTrue(len(f) == 2, 'f = '+repr(f))

        for g in f:
            self.assertTrue(g.equals(g.copy(), verbose=True))
            self.assertTrue(len(g.auxiliary_coordinates) == 4)
#            g.dump()

        g = f[0]
        for axis in ('X', 'Y', 'Z'):
            coord = g.construct('axis='+axis)
            self.assertTrue(coord.has_node_count(), 'axis='+axis)
            self.assertTrue(coord.has_part_node_count(), 'axis='+axis)
            self.assertTrue(coord.has_interior_ring(), 'axis='+axis)

        cfdm.write(f, self.tempfilename, Conventions='CF-1.8', verbose=False)
#        cfdm.write(f, 'delme.nc', Conventions='CF-1.8', verbose=False)

        f2 = cfdm.read(self.tempfilename, verbose=False)

        self.assertTrue(len(f2) == 2, 'f2 = '+repr(f2))
        
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b, verbose=True))
    #--- End: def

#--- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
    
