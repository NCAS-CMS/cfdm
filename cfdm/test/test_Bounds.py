import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DimensionCoordinateTest(unittest.TestCase):
    """Unit test for the DimensionCoordinate class."""

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

    def test_Bounds_inherited_properties(self):
        """Test cfdm.Bounds.inherited_properties."""
        b = cfdm.Bounds()

        properties = {"standard_name": "latitude"}
        b._set_component("inherited_properties", properties, copy=False)
        self.assertEqual(b.inherited_properties(), properties)

        c = b.copy()
        self.assertEqual(c.inherited_properties(), properties)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
