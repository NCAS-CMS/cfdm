from __future__ import print_function

import datetime
import inspect
import os
import unittest

import cfdm

class NetCDFTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_netCDF_variable(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.Field()

        f.nc_set_variable('qwerty')
        self.assertTrue(f.nc_has_variable())
        self.assertTrue(f.nc_get_variable() == 'qwerty')
        self.assertTrue(f.nc_get_variable(default=None) == 'qwerty')
        self.assertTrue(f.nc_del_variable() == 'qwerty')
        self.assertFalse(f.nc_has_variable())
        self.assertTrue(f.nc_get_variable(default=None) == None)
        self.assertTrue(f.nc_del_variable(default=None) == None)
    #--- End: def

    def test_netCDF_dimension(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.DomainAxis()
        
        d.nc_set_dimension('qwerty')
        self.assertTrue(d.nc_has_dimension())
        self.assertTrue(d.nc_get_dimension() == 'qwerty')
        self.assertTrue(d.nc_get_dimension(default=None) == 'qwerty')
        self.assertTrue(d.nc_del_dimension() == 'qwerty')
        self.assertFalse(d.nc_has_dimension())
        self.assertTrue(d.nc_get_dimension(default=None) == None)
        self.assertTrue(d.nc_del_dimension(default=None) == None)
    #--- End: def

    def test_netCDF_sample_dimension(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.Count()
        
        d.nc_set_sample_dimension('qwerty')
        self.assertTrue(d.nc_has_sample_dimension())
        self.assertTrue(d.nc_get_sample_dimension() == 'qwerty')
        self.assertTrue(d.nc_get_sample_dimension(default=None) == 'qwerty')
        self.assertTrue(d.nc_del_sample_dimension() == 'qwerty')
        self.assertFalse(d.nc_has_sample_dimension())
        self.assertTrue(d.nc_get_sample_dimension(default=None) == None)
        self.assertTrue(d.nc_del_sample_dimension(default=None) == None)
    #--- End: def


    def test_netCDF_data_variable(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

#        f = cfdm.Field()
#
#        self.assertTrue(f.nc_global_attributes() == set())
#        f.nc_set_global_attributes(['qwerty', 'asdf'])
#        self.assertTrue(f.nc_global_attributes() == set(['qwerty', 'asdf']))
#        f.nc_set_global_attributes(['zxc'])
#        self.assertTrue(f.nc_global_attributes() == set(['qwerty', 'asdf', 'zxc']))
#        self.assertTrue(f.nc_clear_global_attributes() == set(['qwerty', 'asdf', 'zxc']))
#        self.assertTrue(f.nc_global_attributes() == set())
#
#        f = cfdm.Field()
#
#        self.assertTrue(f.nc_clear_global_attributes() == set())

        # Unlimited dimensions
        f = cfdm.Field()

        self.assertTrue(f.nc_unlimited_dimensions() == set())
        f.nc_set_unlimited_dimensions(['qwerty', 'asdf'])
        self.assertTrue(f.nc_unlimited_dimensions() == set(['qwerty', 'asdf']))
        f.nc_set_unlimited_dimensions(['zxc'])
        self.assertTrue(f.nc_unlimited_dimensions() == set(['qwerty', 'asdf', 'zxc']))
        self.assertTrue(f.nc_clear_unlimited_dimensions() == set(['qwerty', 'asdf', 'zxc']))
        self.assertTrue(f.nc_unlimited_dimensions() == set())
       
        f = cfdm.Field()

        self.assertTrue(f.nc_clear_unlimited_dimensions() == set())

        # Global attributes
        f = cfdm.Field()

        f.nc_set_global_attributes({'Conventions': None, 'project': None})
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None}) #set(['Conventions', 'project']))
        
        f.nc_set_global_attributes({'project': None, 'comment': None})
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None, 'comment': None}) #set(['Conventions', 'project', 'comment']), f.nc_global_attributes())
        
        x = f.nc_clear_global_attributes()
        self.assertTrue(x == {'Conventions': None, 'project': None, 'comment': None}) #set(['Conventions', 'project', 'comment']), repr(x))
        self.assertTrue(f.nc_global_attributes() == {}) #set())
        
        f.nc_set_global_attributes({'Conventions': None, 'project': None}) #['Conventions', 'project'])
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None}) #set(['Conventions', 'project']))
    #--- End: def

#
#    def test_Field_nc_unlimited_dimensions(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = cfdm.Field()
#
#        f.nc_set_unlimited_dimensions(['Conventions', 'project'])
#        self.assertTrue(f.nc_unlimited_dimensions() == set(['Conventions', 'project']))
#        
#        f.nc_set_unlimited_dimensions(['project', 'comment'])
#        self.assertTrue(f.nc_unlimited_dimensions() == set(['Conventions', 'project', 'comment']), f.nc_unlimited_dimensions())
#        
#        x = f.nc_clear_unlimited_dimensions()
#        self.assertTrue(x == set(['Conventions', 'project', 'comment']), repr(x))
#        self.assertTrue(f.nc_unlimited_dimensions() == set())
#        
#        f.nc_set_unlimited_dimensions(['Conventions', 'project'])
#        self.assertTrue(f.nc_unlimited_dimensions() == set(['Conventions', 'project']))
#    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
