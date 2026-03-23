import datetime
import faulthandler
import os
import unittest

import fsspec

faulthandler.enable()  # to debug seg faults and timeouts


import cfdm

warnings = False


kerchunk_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "example_field_0.kerchunk"
)

fs = fsspec.filesystem("reference", fo=kerchunk_file)
kerchunk_mapper = fs.get_mapper()


class read_writeTest(unittest.TestCase):
    """Test the reading and writing of field constructs from/to disk."""

    netcdf = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "example_field_0.nc"
    )
    kerchunk = kerchunk_mapper

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows: cfdm.LOG_LEVEL('DEBUG')
        #
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_kerchunk_read(self):
        """Test cfdm.read with Kerchunk."""
        f = cfdm.read(self.netcdf)[0]

        k = cfdm.read(self.kerchunk)
        self.assertEqual(len(k), 1)
        self.assertTrue(k[0].equals(f))

        k = cfdm.read([self.kerchunk, self.kerchunk])
        self.assertEqual(len(k), 2)
        self.assertTrue(k[0].equals(k[-1]))

        k = cfdm.read([self.kerchunk, self.kerchunk, self.netcdf])
        self.assertEqual(len(k), 3)
        self.assertTrue(k[0].equals(k[-1]))
        self.assertTrue(k[1].equals(k[-1]))

    def test_kerchunk_original_filenames(self):
        """Test original_filenames with Kerchunk."""
        k = cfdm.read(self.kerchunk)[0]
        self.assertEqual(k.get_original_filenames(), set())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
