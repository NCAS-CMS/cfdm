import datetime
import os
import unittest

import numpy

import cfdm


class DimensionCoordinateTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')
        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')

        dim1 = cfdm.DimensionCoordinate()
        dim1.set_property('standard_name', 'latitude')
        a = numpy.array(
            [-30, -23.5, -17.8123, -11.3345, -0.7, -0.2, 0, 0.2, 0.7, 11.30003,
             17.8678678, 23.5, 30]
        )
        dim1.set_data(cfdm.Data(a, 'degrees_north'))
        bounds = cfdm.Bounds()
        b = numpy.empty(a.shape + (2,))
        b[:, 0] = a - 0.1
        b[:, 1] = a + 0.1
        bounds.set_data(cfdm.Data(b))
        dim1.set_bounds(bounds)
        self.dim = dim1

    def test_DimensionCoordinate__repr__str__dump(self):
        f = cfdm.read(self.filename)[0]
        x = f.dimension_coordinates('grid_latitude').value()

        _ = repr(x)
        _ = str(x)
        self.assertIsInstance(x.dump(display=False), str)
        self.assertIsInstance(x.dump(display=False, _key='qwerty'), str)

    def test_DimensionCoordinate_set_data(self):
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

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
