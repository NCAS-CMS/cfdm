import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class LinearSubarrayTest(unittest.TestCase):
    """Unit test for the LinearSubarrayArray class."""

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

    def test_LinearSubarray_compressed_dimensions(self):
        """Test `LinearSubarray.compressed_dimensions`."""
        cd = {1: (1,)}
        x = cfdm.LinearSubarray(compressed_dimensions=cd)
        self.assertEqual(x.compressed_dimensions(), cd)

        x = cfdm.LinearSubarray()
        with self.assertRaises(ValueError):
            x.compressed_dimensions()

    def test_LinearSubarray_get_filename(self):
        """Test LinearSubarray.get_filename."""
        x = cfdm.LinearSubarray(
            data=123, parameters={}, dependent_tie_points={}
        )
        with self.assertRaises(AttributeError):
            x.get_filename()

    def test_LinearSubarray_get_filenames(self):
        """Test LinearSubarray.get_filenames."""
        x = cfdm.LinearSubarray(
            data=123, parameters={}, dependent_tie_points={}
        )
        self.assertEqual(x.get_filenames(), ())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
