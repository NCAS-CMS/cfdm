import datetime
import os
import unittest

import cfdm


class NodeCountPropertiesTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.geometry_interior_ring_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'geometry_interior_ring.nc')
        self.geometry_interior_ring_file_2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'geometry_interior_ring_2.nc')

    def test_NodeCountProperties__repr__str__dump(self):
        f = cfdm.read(self.geometry_interior_ring_file)[0]

        coord = f.construct('axis=X')
        self.assertTrue(coord.has_node_count())

        n = coord.get_node_count()

        _ = repr(n)
        _ = str(n)
        self.assertIsInstance(n.dump(display=False), str)

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
