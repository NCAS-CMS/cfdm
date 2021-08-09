import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_CoordinateReference.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tempfile1,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class CoordinateReferenceTest(unittest.TestCase):
    """Unit test for the CoordinateReference class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, f"f={f!r}")
        self.f = f[0]

    def test_CoordinateReference__repr__str__dump_construct_type(self):
        """Test all means of CoordinateReference inspection."""
        f = self.f

        for cr in f.coordinate_references().values():
            _ = repr(cr)
            _ = str(cr)
            self.assertIsInstance(cr.dump(display=False), str)
            self.assertEqual(cr.construct_type, "coordinate_reference")

    def test_CoordinateReference_equals(self):
        """Test the equality-testing CoordinateReference method."""
        # Create a vertical grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=("coord1",),
            coordinate_conversion=cfdm.CoordinateConversion(
                parameters={
                    "standard_name": "atmosphere_hybrid_height_coordinate"
                },
                domain_ancillaries={"a": "aux0", "b": "aux1", "orog": "orog"},
            ),
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=["coord1", "fred", "coord3"],
            coordinate_conversion=cfdm.CoordinateConversion(
                parameters={
                    "grid_mapping_name": "rotated_latitude_longitude",
                    "grid_north_pole_latitude": 38.0,
                    "grid_north_pole_longitude": 190.0,
                }
            ),
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        datum = cfdm.Datum(parameters={"earth_radius": 6371007})
        conversion = cfdm.CoordinateConversion(
            parameters={
                "grid_mapping_name": "rotated_latitude_longitude",
                "grid_north_pole_latitude": 38.0,
                "grid_north_pole_longitude": 190.0,
            }
        )

        t = cfdm.CoordinateReference(
            coordinate_conversion=conversion,
            datum=datum,
            coordinates=["x", "y", "lat", "lon"],
        )

        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=["coord1", "fred", "coord3"],
            coordinate_conversion=cfdm.CoordinateConversion(
                parameters={
                    "grid_mapping_name": "albers_conical_equal_area",
                    "standard_parallel": [-30, 10],
                    "longitude_of_projection_origin": 34.8,
                    "false_easting": -20000,
                    "false_northing": -30000,
                }
            ),
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

        # Create a horizontal grid mapping coordinate reference
        t = cfdm.CoordinateReference(
            coordinates=["coord1", "fred", "coord3"],
            coordinate_conversion=cfdm.CoordinateConversion(
                parameters={
                    "grid_mapping_name": "albers_conical_equal_area",
                    "standard_parallel": cfdm.Data([-30, 10]),
                    "longitude_of_projection_origin": 34.8,
                    "false_easting": -20000,
                    "false_northing": -30000,
                }
            ),
        )
        self.assertTrue(t.equals(t.copy(), verbose=3))

    def test_CoordinateConversion(self):
        """Test a CoordinateReference coordinate conversion element."""
        f = self.f.copy()

        cr = f.construct("standard_name:atmosphere_hybrid_height_coordinate")
        cc = cr.coordinate_conversion
        _ = repr(cc)
        _ = str(cc)

        domain_ancillaries = cc.domain_ancillaries()
        self.assertEqual(len(domain_ancillaries), 3)

        for key, value in domain_ancillaries.items():
            self.assertTrue(cc.has_domain_ancillary(key))
            self.assertEqual(cc.get_domain_ancillary(key), value)
            _ = cc.del_domain_ancillary(key)
            self.assertFalse(cc.has_domain_ancillary(key))
            self.assertIsNone(cc.get_domain_ancillary(key, None))
            self.assertIsNone(cc.del_domain_ancillary(key, None))
            cc.set_domain_ancillary(key, _)
            self.assertTrue(cc.has_domain_ancillary(key))
            self.assertEqual(cc.get_domain_ancillary(key), value)

        cr = f.construct("grid_mapping_name:rotated_latitude_longitude")
        cc = cr.coordinate_conversion
        _ = repr(cc)
        _ = str(cc)

        parameters = cc.parameters()
        self.assertEqual(len(parameters), 3, parameters)

        for key, value in parameters.items():
            self.assertTrue(cc.has_parameter(key))
            self.assertEqual(cc.get_parameter(key), value)
            _ = cc.del_parameter(key)
            self.assertFalse(cc.has_parameter(key))
            self.assertIsNone(cc.get_parameter(key, None))
            self.assertIsNone(cc.del_parameter(key, None))
            cc.set_parameter(key, _)
            self.assertTrue(cc.has_parameter(key))
            self.assertEqual(cc.get_parameter(key), value)

        _ = cr.del_coordinate_conversion()
        self.assertTrue(_.equals(cc))

    def test_Datum(self):
        """Test a CoordinateReference datum component."""
        f = self.f.copy()

        cr = f.construct("standard_name:atmosphere_hybrid_height_coordinate")
        d = cr.datum
        _ = repr(d)
        _ = str(d)

        parameters = d.parameters()
        self.assertEqual(len(parameters), 1, parameters)

        for key, value in parameters.items():
            self.assertTrue(d.has_parameter(key))
            self.assertEqual(d.get_parameter(key), value)
            _ = d.del_parameter(key)
            self.assertFalse(d.has_parameter(key))
            self.assertIsNone(d.get_parameter(key, None))
            self.assertIsNone(d.del_parameter(key, None))
            d.set_parameter(key, _)
            self.assertTrue(d.has_parameter(key))
            self.assertEqual(d.get_parameter(key), value)

        _ = cr.del_datum()
        self.assertTrue(_.equals(d))

        f = self.f.copy()
        key = f.construct_key("grid_mapping_name:rotated_latitude_longitude")
        f.del_construct(key)
        cr = f.construct("standard_name:atmosphere_hybrid_height_coordinate")
        cr.datum.nc_set_variable("my_name")
        cfdm.write(f, tempfile1)

    def test_CoordinateReference_parameters(self):
        """TODO DOCS."""
        f = self.f.copy()

        cr = f.construct("grid_mapping_name:rotated_latitude_longitude")

        cr.datum.set_parameter("test", 999)
        cr.coordinate_conversion.set_parameter("test", 111)

        with self.assertRaises(ValueError):
            cfdm.write(f, tempfile1)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
