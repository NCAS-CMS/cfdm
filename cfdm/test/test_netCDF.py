from __future__ import print_function

import datetime
import inspect
import os
import tempfile
import unittest

import cfdm


class NetCDFTest(unittest.TestCase):
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

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, 'f={!r}'.format(f))
        self.f = f[0]

        (fd, self.tempfilename) = tempfile.mkstemp(
            suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)

        self.test_only = []

    def tearDown(self):
        os.remove(self.tempfilename)

    def test_netCDF_variable_dimension(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.Field()

        f.nc_set_variable('qwerty')
        self.assertTrue(f.nc_has_variable())
        self.assertEqual(f.nc_get_variable(), 'qwerty')
        self.assertEqual(f.nc_get_variable(default=None), 'qwerty')
        self.assertEqual(f.nc_del_variable(), 'qwerty')
        self.assertFalse(f.nc_has_variable())
        self.assertIsNone(f.nc_get_variable(default=None))
        self.assertIsNone(f.nc_del_variable(default=None))

        d = cfdm.DomainAxis()

        d.nc_set_dimension('qwerty')
        self.assertTrue(d.nc_has_dimension())
        self.assertEqual(d.nc_get_dimension(), 'qwerty')
        self.assertEqual(d.nc_get_dimension(default=None), 'qwerty')
        self.assertEqual(d.nc_del_dimension(), 'qwerty')
        self.assertFalse(d.nc_has_dimension())
        self.assertIsNone(d.nc_get_dimension(default=None))
        self.assertIsNone(d.nc_del_dimension(default=None))

        d = cfdm.Count()

        d.nc_set_sample_dimension('qwerty')
        self.assertTrue(d.nc_has_sample_dimension())
        self.assertEqual(d.nc_get_sample_dimension(), 'qwerty')
        self.assertEqual(d.nc_get_sample_dimension(default=None), 'qwerty')
        self.assertEqual(d.nc_del_sample_dimension(), 'qwerty')
        self.assertFalse(d.nc_has_sample_dimension())
        self.assertIsNone(d.nc_get_sample_dimension(default=None))
        self.assertIsNone(d.nc_del_sample_dimension(default=None))

        # ------------------------------------------------------------
        # Global attributes
        # ------------------------------------------------------------
        # values keyword
        f = cfdm.Field()

        f.nc_set_global_attribute('Conventions', 'CF-1.8')
        f.nc_set_global_attribute('project')
        f.nc_set_global_attribute('foo')
        f.set_property('Conventions', 'Y')
        f.set_property('project', 'X')
        self.assertEqual(f.nc_global_attributes(values=True),
                         {'Conventions': 'CF-1.8',
                          'project': 'X',
                          'foo': None})
        
        f = cfdm.Field()
        self.assertEqual(f.nc_clear_global_attributes(), {})

        f.nc_set_global_attribute('Conventions')
        f.nc_set_global_attribute('project', 'X')
        self.assertEqual(f.nc_global_attributes(), {'Conventions': None,
                                                    'project': 'X'})

        f.nc_set_global_attribute('project')
        f.nc_set_global_attribute('comment', None)
        self.assertEqual(f.nc_global_attributes(), {'Conventions': None,
                                                    'project': None,
                                                    'comment': None})

        self.assertEqual(f.nc_clear_global_attributes(), {'Conventions': None,
                                                          'project': None,
                                                          'comment': None})
        self.assertEqual(f.nc_global_attributes(), {})

        f.nc_set_global_attribute('Conventions')
        f.nc_set_global_attribute('project')
        self.assertEqual(f.nc_global_attributes(), {'Conventions': None,
                                                    'project': None})

        _ = f.nc_clear_global_attributes()
        f.nc_set_global_attributes({})
        self.assertEqual(f.nc_global_attributes(), {})

        f.nc_set_global_attributes({'comment': 123}, copy=False)
        self.assertEqual(f.nc_global_attributes(), {'comment': 123})

        f.nc_set_global_attributes({'comment': None, 'foo': 'bar'})
        self.assertEqual(f.nc_global_attributes(), {'comment': None,
                                                    'foo': 'bar'})

        f = cfdm.Field()
        f.set_properties({'foo': 'bar', 'comment': 'variable comment'})
        f.nc_set_variable('tas')
        d = f.set_construct(cfdm.DomainAxis(2))
        f.set_data(cfdm.Data([8, 9]), axes=[d])

        f2 = f.copy()
        f2.nc_set_variable('ua')

        cfdm.write([f, f2], 'tempfilename.nc',
                   file_descriptors={'comment': 'global comment',
                                     'qwerty': 'asdf'})

        g = cfdm.read('tempfilename.nc')
        self.assertEqual(len(g), 2)

        for x in g:
            self.assertEqual(x.properties(), {'comment': 'variable comment',
                                              'foo': 'bar',
                                              'qwerty': 'asdf',
                                              'Conventions': 'CF-'+cfdm.CF()})
            self.assertEqual(x.nc_global_attributes(),
                             {'comment': 'global comment',
                              'qwerty': None,
                              'Conventions': None})
            
        cfdm.write(g, 'tempfilename2.nc')
        h = cfdm.read('tempfilename2.nc')
        for x, y in zip(h, g):
            self.assertEqual(x.properties(), y.properties())
            self.assertEqual(x.nc_global_attributes(),
                             y.nc_global_attributes())
            self.assertTrue(x.equals(y, verbose=3))
            self.assertTrue(y.equals(x, verbose=3))

        g[1].nc_set_global_attribute('comment', 'different comment')
        cfdm.write(g, 'tempfilename3.nc')
        h = cfdm.read('tempfilename3.nc')
        for x, y in zip(h, g):
            self.assertEqual(x.properties(), y.properties())
            self.assertEqual(x.nc_global_attributes(), {'comment': None,
                                                        'qwerty': None,
                                                        'Conventions': None})
            self.assertTrue(x.equals(y, verbose=3))
            self.assertTrue(y.equals(x, verbose=3))
#        os.remove('tempfilename.nc')


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
