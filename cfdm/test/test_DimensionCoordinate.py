import datetime
import faulthandler
import os
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DimensionCoordinateTest(unittest.TestCase):
    """Unit test for the DimensionCoordinate class."""

    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
    )

    dim = cfdm.DimensionCoordinate()
    dim.set_property("standard_name", "latitude")
    a = numpy.array(
        [
            -30,
            -23.5,
            -17.8123,
            -11.3345,
            -0.7,
            -0.2,
            0,
            0.2,
            0.7,
            11.30003,
            17.8678678,
            23.5,
            30,
        ]
    )
    dim.set_data(cfdm.Data(a, "degrees_north"))
    bounds = cfdm.Bounds()
    b = numpy.empty(a.shape + (2,))
    b[:, 0] = a - 0.1
    b[:, 1] = a + 0.1
    bounds.set_data(cfdm.Data(b))
    dim.set_bounds(bounds)

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_DimensionCoordinate__repr__str__dump(self):
        """Test all means of DimensionCoordinate inspection."""
        f = cfdm.read(self.filename)[0]
        x = f.dimension_coordinates("grid_latitude").value()

        _ = repr(x)
        _ = str(x)
        self.assertIsInstance(x.dump(display=False), str)
        self.assertIsInstance(x.dump(display=False, _key="qwerty"), str)

    def test_DimensionCoordinate__init__(self):
        """Test the constructor of DimensionCoordinate."""
        cfdm.DimensionCoordinate(source="qwerty")

    def test_DimensionCoordinate_set_data(self):
        """Test the `set_data` DimensionCoordinate method."""
        x = cfdm.DimensionCoordinate()

        y = x.set_data(cfdm.Data([1, 2, 3]))
        self.assertIsNone(y)
        self.assertTrue(x.has_data())

        # Test inplace
        x.del_data()
        y = x.set_data(cfdm.Data([1, 2, 3]), inplace=False)
        self.assertIsInstance(y, cfdm.DimensionCoordinate)
        self.assertFalse(x.has_data())
        self.assertTrue(y.has_data())

        # Exceptions should be raised for 0-d and N-d (N>=2) data
        with self.assertRaises(Exception):
            y = x.set_data(cfdm.Data([[1, 2, 3]]))

        with self.assertRaises(Exception):
            y = x.set_data(cfdm.Data(1))

    def test_DimensionCoordinate_climatology(self):
        """Test the climatology DimensionCoordinate methods."""
        x = cfdm.DimensionCoordinate()

        self.assertFalse(x.is_climatology())
        self.assertIsNone(x.get_climatology(None))
        x.set_climatology(False)
        self.assertFalse(x.is_climatology())
        self.assertFalse(x.get_climatology())
        x.set_climatology(True)
        self.assertTrue(x.is_climatology())
        self.assertTrue(x.del_climatology())
        self.assertIsNone(x.del_climatology(None))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
