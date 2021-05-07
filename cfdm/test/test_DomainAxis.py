import datetime
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DomainTest(unittest.TestCase):
    """TODO DOCS."""

    d = cfdm.DomainAxis(size=99)
    d.nc_set_dimension("ncdim")

    def setUp(self):
        """TODO DOCS."""
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

    def test_DomainAxis__repr__str_construct_type(self):
        """TODO DOCS."""
        d = self.d

        repr(d)
        str(d)
        self.assertEqual(d.construct_type, "domain_axis")

    def test_DomainAxis_source(self):
        """TODO DOCS."""
        d = self.d

        self.assertTrue(d.equals(cfdm.DomainAxis(source=d)))

        self.assertIsInstance(
            cfdm.DomainAxis(source="QWERTY"), cfdm.DomainAxis
        )

    def test_DomainAxis_equals(self):
        """TODO DOCS."""
        d = self.d
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

    def test_DomainAxis_size(self):
        """TODO DOCS."""
        d = self.d.copy()
        d.set_size(100)

        self.assertTrue(d.has_size())
        self.assertEqual(d.get_size(), 100)
        self.assertEqual(d.del_size(), 100)
        self.assertIsNone(d.get_size(None))
        self.assertIsNone(d.del_size(None))
        self.assertFalse(d.has_size())

    def test_DomainAxis_unlimited(self):
        """TODO DOCS."""
        d = cfdm.DomainAxis()
        d.set_size(99)

        self.assertFalse(d.nc_is_unlimited())

        d.nc_set_unlimited(False)
        self.assertFalse(d.nc_is_unlimited())

        d.nc_set_unlimited(True)
        self.assertTrue(d.nc_is_unlimited())

        d.nc_set_unlimited(False)
        self.assertFalse(d.nc_is_unlimited())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
