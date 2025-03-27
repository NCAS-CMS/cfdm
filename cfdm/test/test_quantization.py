import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

import netCDF4
import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

# Set up temporary files
n_tmpfiles = 2
tmpfiles = [
    tempfile.mkstemp("_test_quantization.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
[tmpfile1, tmpfile2] = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class read_writeTest(unittest.TestCase):
    """Test the reading and writing of field constructs from/to disk."""

    f1 = cfdm.example_field(1)

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
        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

        self.string_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "string_char.nc"
        )

        self.netcdf3_fmts = [
            "NETCDF3_CLASSIC",
            "NETCDF3_64BIT",
            "NETCDF3_64BIT_OFFSET",
            "NETCDF3_64BIT_DATA",
        ]
        self.netcdf4_fmts = ["NETCDF4", "NETCDF4_CLASSIC"]
        self.netcdf_fmts = self.netcdf3_fmts + self.netcdf4_fmts

    def test_quantization(self):
        """Test reading, writing, and storing quantization."""
        f = self.f1.copy()
        # Add some precision to the data
        f.data[...] = f.array + 0.123456789

        self.assertIsNone(f.get_quantize_on_write(None))
        self.assertIsNone(f.del_quantize_on_write(None))

        # Set a quantisation instruction
        q0 = cfdm.Quantization(
            {
                "algorithm": "digitround",
                "quantization_nsd": 9,
                "implementation": "foobar",
            }
        )
        nsd = 2
        self.assertIsNone(
            f.set_quantize_on_write(
                quantization=q0,
                algorithm="granular_bitround",
                quantization_nsd=nsd,
            )
        )
        self.assertTrue(
            f.get_quantize_on_write().equals(
                cfdm.Quantization(
                    {"algorithm": "granular_bitround", "quantization_nsd": nsd}
                )
            )
        )

        # Write the field and read it back in
        cfdm.write(f, tmpfile1)
        g = cfdm.read(tmpfile1)[0]

        # Check that f and g have different data (i.e. that
        # quantization occured on disk, and not in f in memory)
        self.assertFalse(np.allclose(f.data, g.data))

        # Check that g has the correct Quantisation component
        q = g.get_quantization()
        self.assertIsInstance(q, cfdm.Quantization)
        self.assertEqual(
            q.parameters(),
            {
                "_QuantizeGranularBitRoundNumberOfSignificantDigits": nsd,
                "algorithm": "granular_bitround",
                "implementation": f"libnetcdf version {netCDF4.__netcdf4libversion__}",
                "quantization_nsd": nsd,
            },
        )

        # Write the quantized field and read it back in
        cfdm.write(g, tmpfile2)
        h = cfdm.read(tmpfile2)[0]

        # Check that h and g are equal
        self.assertTrue(h.equals(g))

        # Check that h and g are not equal when they only differ by
        # their quantization components
        h._set_quantization(q0)
        self.assertFalse(h.equals(g))

        # Can't set_quantize_on_write when already quantized
        with self.assertRaises(ValueError):
            h.set_quantize_on_write()


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
