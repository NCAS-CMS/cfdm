from __future__ import print_function

import datetime
import inspect
import os
import tempfile
import unittest

import cfdm

class NetCDFTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        (fd, self.tempfilename) = tempfile.mkstemp(suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)
        
        self.test_only = []
    #--- End: def

    def tearDown(self):
        os.remove(self.tempfilename)
    #--- End: def
    
    def test_netCDF_variable_dimension(self):
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

        d = cfdm.DomainAxis()
        
        d.nc_set_dimension('qwerty')
        self.assertTrue(d.nc_has_dimension())
        self.assertTrue(d.nc_get_dimension() == 'qwerty')
        self.assertTrue(d.nc_get_dimension(default=None) == 'qwerty')
        self.assertTrue(d.nc_del_dimension() == 'qwerty')
        self.assertFalse(d.nc_has_dimension())
        self.assertTrue(d.nc_get_dimension(default=None) == None)
        self.assertTrue(d.nc_del_dimension(default=None) == None)

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


    def test_netCDF_global_unlimited(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # ------------------------------------------------------------
        # Unlimited dimensions
        # ------------------------------------------------------------
        f = cfdm.Field()
        self.assertTrue(f.nc_clear_unlimited_dimensions() == set())

        f = cfdm.Field()
        f.nc_set_unlimited_dimensions(())
        
        f = cfdm.Field()
        self.assertTrue(f.nc_unlimited_dimensions() == set())
        f.nc_set_unlimited_dimensions(['qwerty', 'asdf'])
        self.assertTrue(f.nc_unlimited_dimensions() == set(['qwerty', 'asdf']))
        f.nc_set_unlimited_dimensions(['zxc'])
        self.assertTrue(f.nc_unlimited_dimensions() == set(['qwerty', 'asdf', 'zxc']))
        self.assertTrue(f.nc_clear_unlimited_dimensions() == set(['qwerty', 'asdf', 'zxc']))
        self.assertTrue(f.nc_unlimited_dimensions() == set())
       
        # ------------------------------------------------------------
        # Global attributes
        # ------------------------------------------------------------
        f = cfdm.Field()
        self.assertTrue(f.nc_clear_global_attributes() == {})
        
        f = cfdm.Field()
        f.nc_set_global_attributes(())

        f = cfdm.Field()
        f.nc_set_global_attributes()
        
        f = cfdm.Field()
        f.nc_set_global_attributes({'Conventions': None, 'project': None})
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None})
        
        f.nc_set_global_attributes({'project': None, 'comment': None})
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None, 'comment': None})
        
        self.assertTrue(f.nc_clear_global_attributes() == {'Conventions': None, 'project': None, 'comment': None})
        self.assertTrue(f.nc_global_attributes() == {})
        
        f.nc_set_global_attributes(['Conventions', 'project'])
        self.assertTrue(f.nc_global_attributes() == {'Conventions': None, 'project': None})


        f = cfdm.Field()
        f.set_properties({'foo': 'bar', 'comment': 'variable comment'})
        d = f.set_construct(cfdm.DomainAxis(2))
        f.set_data(cfdm.Data([8, 9]), axes=[d])

        cfdm.write(f, self.tempfilename, file_descriptors={'comment': 'global comment',
                                                           'qwerty': 'asdf'})
        g = cfdm.read(self.tempfilename)[0]

        self.assertTrue(g.properties() == {'foo': 'bar',
                                           'comment': 'variable comment',
                                           'qwerty': 'asdf',
                                           'Conventions': 'CF-1.7'})
        self.assertTrue(g.nc_global_attributes() == {'comment': 'global comment',
                                                     'qwerty': None,
                                                     'Conventions': None})

        cfdm.write(g, 'tempfilename.nc')
        h = cfdm.read('tempfilename.nc')[0]
        self.assertTrue(h.properties()           == g.properties())
        self.assertTrue(h.nc_global_attributes() == g.nc_global_attributes())
        self.assertTrue(h.equals(g, verbose=True))
        self.assertTrue(g.equals(h, verbose=True))
        os.remove('tempfilename.nc')
   #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
