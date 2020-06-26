from __future__ import print_function
import atexit
import datetime
import os
import tempfile
import unittest

import netCDF4
import netcdf_flattener

import cfdm


n_tmpfiles = 2
tmpfiles = [tempfile.mktemp('_test_groups.nc', dir=os.getcwd())
            for i in range(n_tmpfiles)]
(ungrouped_file,
 grouped_file,
) = tmpfiles

def _remove_tmpfiles():
    '''Remove temporary files created during tests.

    '''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass

atexit.register(_remove_tmpfiles)


class GroupsTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

    def test_groups(self):
        f = cfdm.example_field(1)
        
#        # Add a second grid mapping    
#        datum = cfdm.Datum(parameters={'earth_radius': 7000000})
#        conversion = cfdm.CoordinateConversion(
#            parameters={'grid_mapping_name': 'latitude_longitude'})
#        
#        grid = cfdm.CoordinateReference(
#            coordinate_conversion=conversion,
#            datum=datum,
#            coordinates=['auxiliarycoordinate0', 'auxiliarycoordinate1']
#        )
#
#        f.set_construct(grid)
#        
#        grid0 = f.construct('grid_mapping_name:rotated_latitude_longitude')
#        grid0.del_coordinate('auxiliarycoordinate0')
#        grid0.del_coordinate('auxiliarycoordinate1')
#        
#        f.dump()
        
        ungrouped_file = 'ungrouped1.nc'
        cfdm.write(f, ungrouped_file)
        g = cfdm.read(ungrouped_file)[0]
        self.assertTrue(f.equals(g, verbose=2))

        grouped_file = 'delme1.nc'a
        filename = grouped_file

        # ------------------------------------------------------------
        # Move the field construct to the /forecast/model group
        # ------------------------------------------------------------
        g.nc_set_variable_groups(['forecast', 'model'])
        cfdm.write(g, filename)

        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.nc_get_variable(),
            nc.groups['forecast'].groups['model'].variables
        )
        nc.close()
        
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
        # ------------------------------------------------------------
        # Move the time dimension coordinate to the /forecast group
        # ------------------------------------------------------------
        g.construct('time').nc_set_variable_groups(['forecast'])
        cfdm.write(g, filename)
        
        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.construct('time').nc_get_variable(),
            nc.groups['forecast'].variables
        )
        nc.close()
        
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
        # ------------------------------------------------------------
        # Move a cell measure to the /forecast group
        # ------------------------------------------------------------
        c = g.construct('measure:area')
        c.nc_set_variable_groups(['forecast'])
        cfdm.write(g, filename)

        # Check that the variable is in the right group
        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.construct('measure:area').nc_get_variable(),
            nc.groups['forecast'].variables)
        nc.close()

        # Check that the field construct hasn't changed
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
        # ------------------------------------------------------------
        # Move a domain ancillary to the /forecast group
        # ------------------------------------------------------------
        c = g.construct('surface_altitude')
        c.nc_set_variable_groups(['forecast'])
        cfdm.write(g, filename)

        # Check that the variable is in the right group
        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.construct('surface_altitude').nc_get_variable(),
            nc.groups['forecast'].variables)
        nc.close()

        # Check that the field construct hasn't changed
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
        # ------------------------------------------------------------
        # Move a grid mapping to the /forecast group
        # ------------------------------------------------------------
        c = g.construct('grid_mapping_name:rotated_latitude_longitude')
        c.nc_set_variable_groups(['forecast'])
        cfdm.write(g, filename)
        
        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.construct('grid_mapping_name:rotated_latitude_longitude').nc_get_variable(),
            nc.groups['forecast'].variables)
        nc.close()
        
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
    def test_groups_geometry(self):
        f = cfdm.example_field(6)
                
        ungrouped_file = 'ungrouped1.nc'
        cfdm.write(f, ungrouped_file)
        g = cfdm.read(ungrouped_file)[0]
        self.assertTrue(f.equals(g, verbose=2))

        grouped_file = 'delme1.nc'
        filename = grouped_file

        # ------------------------------------------------------------
        # Move the field construct to the /forecast/model group
        # ------------------------------------------------------------
        g.nc_set_variable_groups(['forecast', 'model'])
        cfdm.write(g, filename)

        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.nc_get_variable(),
            nc.groups['forecast'].groups['model'].variables
        )
        nc.close()
        
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
        # ------------------------------------------------------------
        # Move the geometry container to the /forecast group
        # ------------------------------------------------------------
        g.nc_set_geometry_variable_groups(['forecast'])
        cfdm.write(g, filename)

        # Check that the variable is in the right group
        nc = netCDF4.Dataset(filename, 'r')
        self.assertIn(
            f.nc_get_geometry_variable(),
            nc.groups['forecast'].variables)
        nc.close()

        # Check that the field construct hasn't changed
        h = cfdm.read(filename)
        self.assertEqual(len(h), 1, repr(h))
        self.assertTrue(f.equals(h[0], verbose=2))
        
#--- End: class

#        netcdf_flattener.flatten(i, o)
#
#        o.close()
#
#        h = cfdm.read('tmp.nc')[0]
#
#        h.del_property('flattener_name_mapping_attributes')
#        h.del_property('flattener_name_mapping_variables')
#        h.del_property('flattener_name_mapping_dimensions')


#        i = netCDF4.Dataset(ungrouped_file, 'r')
#        o = netCDF4.Dataset('tmp.nc', 'w')
#
#        netcdf_flattener.flatten(i, o)
#
#        o.close()
#
#        h = cfdm.read('tmp.nc')[0]
#
#        h.del_property('flattener_name_mapping_attributes')
#        h.del_property('flattener_name_mapping_variables')
#        h.del_property('flattener_name_mapping_dimensions')


if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)

