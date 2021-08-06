import datetime
import faulthandler
import os
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class PartNodeCountPropertiesTest(unittest.TestCase):
    """Unit test for the PartNodeCountProperties class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.geometry_interior_ring_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "geometry_interior_ring.nc",
        )
        self.geometry_interior_ring_file_2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "geometry_interior_ring_2.nc",
        )

    def test_PartNodeCountProperties__repr__str__dump(self):
        """Test all means of PartNodeCountProperties inspection."""
        f = cfdm.read(self.geometry_interior_ring_file)[0]

        coord = f.construct("axis=X")
        self.assertTrue(coord.has_part_node_count())

        p = coord.get_part_node_count()

        _ = repr(p)
        _ = str(p)
        self.assertIsInstance(p.dump(display=False), str)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
