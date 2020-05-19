from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm


class CoordinateReferenceTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []


    def test_CoordinateReference__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for cr in f.coordinate_references.values():
            _ = repr(cr)
            _ = str(cr)
            _ = cr.dump(display=False)
            self.assertTrue(cr.construct_type == 'coordinate_reference')


    def test_CoordinateReference_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        # Create a vertical grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=('coord1',),
            coordinate_conversion=cfdm.CoordinateConversion(
                parameters={'standard_name': 'atmosphere_hybrid_height_coordinate'},
                domain_ancillaries={'a': 'aux0', 'b': 'aux1', 'orog': 'orog'})
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=['coord1', 'fred', 'coord3'],
             coordinate_conversion=cfdm.CoordinateConversion(
                 parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                             'grid_north_pole_latitude': 38.0,
                             'grid_north_pole_longitude': 190.0})
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        datum=cfdm.Datum(parameters={'earth_radius': 6371007})
        conversion=cfdm.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'grid_north_pole_latitude': 38.0,
                        'grid_north_pole_longitude': 190.0})

        t = cfdm.CoordinateReference(
            coordinate_conversion=conversion,
            datum=datum,
            coordinates=['x', 'y', 'lat', 'lon']
        )

        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
               coordinates=['coord1', 'fred', 'coord3'],
               coordinate_conversion=cfdm.CoordinateConversion(
                   parameters={'grid_mapping_name': 'albers_conical_equal_area',
                               'standard_parallel': [-30, 10],
                               'longitude_of_projection_origin': 34.8,
                               'false_easting': -20000,
                               'false_northing': -30000})
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
               coordinates=['coord1', 'fred', 'coord3'],
               coordinate_conversion=cfdm.CoordinateConversion(
                   parameters={'grid_mapping_name': 'albers_conical_equal_area',
                               'standard_parallel': cfdm.Data([-30, 10]),
                               'longitude_of_projection_origin': 34.8,
                               'false_easting': -20000,
                               'false_northing': -30000})
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))


    def test_CoordinateConversion(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        cr = f.construct('standard_name:atmosphere_hybrid_height_coordinate')
        cc = cr.coordinate_conversion
        _ = repr(cc)
        _ = str(cc)

        domain_ancillaries = cc.domain_ancillaries()
        self.assertTrue(len(domain_ancillaries) == 3)

        for key, value in domain_ancillaries.items():
            self.assertTrue(cc.has_domain_ancillary(key))
            self.assertTrue(cc.get_domain_ancillary(key) == value)
            _ = cc.del_domain_ancillary(key)
            self.assertFalse(cc.has_domain_ancillary(key))
            self.assertTrue(cc.get_domain_ancillary(key, None) == None)
            self.assertTrue(cc.del_domain_ancillary(key, None) == None)
            cc.set_domain_ancillary(key, _)
            self.assertTrue(cc.has_domain_ancillary(key))
            self.assertTrue(cc.get_domain_ancillary(key) == value)

        cr = f.construct('grid_mapping_name:rotated_latitude_longitude')
        cc = cr.coordinate_conversion
        _ = repr(cc)
        _ = str(cc)

        parameters = cc.parameters()
        self.assertTrue(len(parameters) == 3, parameters)

        for key, value in parameters.items():
            self.assertTrue(cc.has_parameter(key))
            self.assertTrue(cc.get_parameter(key) == value)
            _ = cc.del_parameter(key)
            self.assertFalse(cc.has_parameter(key))
            self.assertTrue(cc.get_parameter(key, None) == None)
            self.assertTrue(cc.del_parameter(key, None) == None)
            cc.set_parameter(key, _)
            self.assertTrue(cc.has_parameter(key))
            self.assertTrue(cc.get_parameter(key) == value)

        _ = cr.del_coordinate_conversion()
        self.assertTrue(_.equals(cc))


    def test_Datum(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        cr = f.construct('standard_name:atmosphere_hybrid_height_coordinate')
        d = cr.datum
        _ = repr(d)
        _ = str(d)

        parameters = d.parameters()
        self.assertTrue(len(parameters) == 1, parameters)

        for key, value in parameters.items():
            self.assertTrue(d.has_parameter(key))
            self.assertTrue(d.get_parameter(key) == value)
            _ = d.del_parameter(key)
            self.assertFalse(d.has_parameter(key))
            self.assertTrue(d.get_parameter(key, None) == None)
            self.assertTrue(d.del_parameter(key, None) == None)
            d.set_parameter(key, _)
            self.assertTrue(d.has_parameter(key))
            self.assertTrue(d.get_parameter(key) == value)

        _ = cr.del_datum()
        self.assertTrue(_.equals(d))

        f = self.f.copy()
        key = f.construct_key('grid_mapping_name:rotated_latitude_longitude')
        f.del_construct(key)
        cr = f.construct('standard_name:atmosphere_hybrid_height_coordinate')
        cr.datum.nc_set_variable('my_name')
        cfdm.write(f, 'delme.nc')


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
