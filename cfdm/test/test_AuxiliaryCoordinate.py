import datetime
import faulthandler
import os
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class AuxiliaryCoordinateTest(unittest.TestCase):
    """Unit test for the AuxiliaryCoordinate class."""

    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
    )

    aux1 = cfdm.AuxiliaryCoordinate()
    aux1.standard_name = "latitude"
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
    aux1.set_data(cfdm.Data(a, "degrees_north"))
    bounds = cfdm.Bounds()
    b = numpy.empty(a.shape + (2,))
    b[:, 0] = a - 0.1
    b[:, 1] = a + 0.1
    bounds.set_data(cfdm.Data(b))
    aux1.set_bounds(bounds)

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

    def test_AuxiliaryCoordinate__repr__str__dump(self):
        """Test all means of AuxiliaryCoordinate inspection."""
        f = cfdm.read(self.filename, verbose=1)[0]
        x = f.auxiliary_coordinates("latitude").value()

        repr(x)
        str(x)
        self.assertIsInstance(x.dump(display=False), str)
        self.assertIsInstance(x.dump(display=False, _title=None), str)

    def test_AuxiliaryCoordinate_bounds(self):
        """Test the bounds keyword argument to AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]

        d = f.dimension_coordinates("grid_longitude").value()
        cfdm.AuxiliaryCoordinate(bounds=d)

    def test_AuxiliaryCoordinate_properties(self):
        """Test the property access methods of AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates("latitude").value()

        x.set_property("long_name", "qwerty")

        self.assertEqual(x.get_property("long_name"), "qwerty")
        self.assertEqual(x.del_property("long_name"), "qwerty")
        self.assertIsNone(x.get_property("long_name", None))
        self.assertIsNone(x.del_property("long_name", None))

    def test_AuxiliaryCoordinate_source(self):
        """Test the source keyword argument to AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]
        d = f.dimension_coordinates("grid_longitude").value()
        cfdm.AuxiliaryCoordinate(source=d)

    def test_AuxiliaryCoordinate_insert_dimension(self):
        """Test the `insert_dimension` method of AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]
        d = f.dimension_coordinates("grid_longitude").value()
        x = cfdm.AuxiliaryCoordinate(source=d)

        self.assertEqual(x.shape, (9,))
        self.assertEqual(x.bounds.shape, (9, 2))

        y = x.insert_dimension(0)
        self.assertEqual(y.shape, (1, 9))
        self.assertEqual(y.bounds.shape, (1, 9, 2), y.bounds.shape)

        x.insert_dimension(-1, inplace=True)
        self.assertEqual(x.shape, (9, 1))
        self.assertEqual(x.bounds.shape, (9, 1, 2), x.bounds.shape)

    def test_AuxiliaryCoordinate_transpose(self):
        """Test the transpose method of AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates("longitude").value()

        bounds = cfdm.Bounds(
            data=cfdm.Data(numpy.arange(9 * 10 * 4).reshape(9, 10, 4))
        )
        x.set_bounds(bounds)

        self.assertEqual(x.shape, (9, 10))
        self.assertEqual(x.bounds.shape, (9, 10, 4))

        y = x.transpose()
        self.assertEqual(y.shape, (10, 9))
        self.assertEqual(y.bounds.shape, (10, 9, 4), y.bounds.shape)

        x.transpose([1, 0], inplace=True)
        self.assertEqual(x.shape, (10, 9))
        self.assertEqual(x.bounds.shape, (10, 9, 4), x.bounds.shape)

    def test_AuxiliaryCoordinate_squeeze(self):
        """Test the squeeze method of AuxiliaryCoordinate."""
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates("longitude").value()

        bounds = cfdm.Bounds(
            data=cfdm.Data(numpy.arange(9 * 10 * 4).reshape(9, 10, 4))
        )
        x.set_bounds(bounds)
        x.insert_dimension(1, inplace=True)
        x.insert_dimension(0, inplace=True)

        self.assertEqual(x.shape, (1, 9, 1, 10))
        self.assertEqual(x.bounds.shape, (1, 9, 1, 10, 4))

        y = x.squeeze()
        self.assertEqual(y.shape, (9, 10))
        self.assertEqual(y.bounds.shape, (9, 10, 4), y.bounds.shape)

        x.squeeze(2, inplace=True)
        self.assertEqual(x.shape, (1, 9, 10))
        self.assertEqual(x.bounds.shape, (1, 9, 10, 4), x.bounds.shape)

    def test_AuxiliaryCoordinate_interior_ring(self):
        """Test the interior ring access AuxiliaryCoordinate methods."""
        c = cfdm.AuxiliaryCoordinate()

        i = cfdm.InteriorRing(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))

        c.set_interior_ring(i)
        self.assertTrue(c.has_interior_ring())
        self.assertIsInstance(c.get_interior_ring(), cfdm.InteriorRing)
        self.assertIsInstance(c.del_interior_ring(None), cfdm.InteriorRing)
        self.assertFalse(c.has_interior_ring())
        self.assertIsNone(c.del_interior_ring(None))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
