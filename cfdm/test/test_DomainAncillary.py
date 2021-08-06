import datetime
import faulthandler
import os
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DomainAncillaryTest(unittest.TestCase):
    """Unit test for the DomainAncillary class."""

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

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

    def test_DomainAncillary__repr__str__dump(self):
        """Test all means of DomainAncillary inspection."""
        f = cfdm.read(self.filename)[0]
        domain_ancillaries = f.domain_ancillaries("ncvar%a")

        x = domain_ancillaries.value()
        _ = repr(x)
        _ = str(x)
        self.assertIsInstance(x.dump(display=False), str)

        self.assertIsInstance(
            x.dump(display=False, _key=domain_ancillaries.key()),
            str,
        )

        x.nc_del_variable()
        self.assertIsInstance(x.dump(display=False), str)

    def test_DomainAncillary_bounds(self):
        """Test the bounds keyword argument to DomainAncillary."""
        f = cfdm.read(self.filename)[0]

        a = f.auxiliary_coordinates("latitude").value()
        cfdm.DomainAncillary(bounds=a)

    def test_DomainAncillary_properties(self):
        """Test the property access methods of DomainAncillary."""
        f = cfdm.read(self.filename)[0]
        x = f.domain_ancillaries("ncvar%a").value()

        x.set_property("long_name", "qwerty")

        self.assertEqual(x.get_property("long_name"), "qwerty")
        self.assertEqual(x.del_property("long_name"), "qwerty")
        self.assertIsNone(x.get_property("long_name", None))
        self.assertIsNone(x.del_property("long_name", None))

    def test_DomainAncillary_insert_dimension(self):
        """Test the `insert_dimension` DomainAncillary method."""
        f = cfdm.read(self.filename)[0]
        d = f.dimension_coordinates("grid_longitude").value()
        x = cfdm.DomainAncillary(source=d)

        self.assertEqual(x.shape, (9,))
        self.assertEqual(x.bounds.shape, (9, 2))

        y = x.insert_dimension(0)
        self.assertEqual(y.shape, (1, 9))
        self.assertEqual(y.bounds.shape, (1, 9, 2), y.bounds.shape)

        x.insert_dimension(-1, inplace=True)
        self.assertEqual(x.shape, (9, 1))
        self.assertEqual(x.bounds.shape, (9, 1, 2), x.bounds.shape)

    def test_DomainAncillary_transpose(self):
        """Test the transpose DomainAncillary method."""
        f = cfdm.read(self.filename)[0]
        a = f.auxiliary_coordinates("longitude").value()
        bounds = cfdm.Bounds(
            data=cfdm.Data(numpy.arange(9 * 10 * 4).reshape(9, 10, 4))
        )
        a.set_bounds(bounds)
        x = cfdm.DomainAncillary(source=a)

        self.assertEqual(x.shape, (9, 10))
        self.assertEqual(x.bounds.shape, (9, 10, 4))

        y = x.transpose()
        self.assertEqual(y.shape, (10, 9))
        self.assertEqual(y.bounds.shape, (10, 9, 4), y.bounds.shape)

        x.transpose([1, 0], inplace=True)
        self.assertEqual(x.shape, (10, 9))
        self.assertEqual(x.bounds.shape, (10, 9, 4), x.bounds.shape)

    def test_DomainAncillary_squeeze(self):
        """Test the squeeze DomainAncillary method."""
        f = cfdm.read(self.filename)[0]
        a = f.auxiliary_coordinates("longitude").value()
        bounds = cfdm.Bounds(
            data=cfdm.Data(numpy.arange(9 * 10 * 4).reshape(9, 10, 4))
        )
        a.set_bounds(bounds)
        x = cfdm.DomainAncillary(source=a)

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


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
