import atexit
import datetime
import faulthandler
import os
import platform
import shutil
import subprocess
import tempfile
import unittest

import netCDF4
import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm
from cfdm.read_write.exceptions import DatasetTypeError, ReadError

warnings = False

# Set up temporary directories
n_tmp = 9
tmpdirs = [
    tempfile.mkdtemp("_test_zarr.zarr", dir=os.getcwd())
    for i in range(n_tmp)
]
[
    tmp1,
    tmp2,
    tmp3,
    tmp4,
    tmp5,
    tmp6,
    tmp7,
    tmp8,
    tmp9,
] = tmpdirs

# Set up temporary files
n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_zarr.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
[tmpfile] = tmpfiles


def _remove_tmpdirs():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass

    for d in tmpdirs:
        try:
            shutil.rmtree(d)
            os.rmdir(d)
        except OSError:
            pass


atexit.register(_remove_tmpdirs)

filename = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
)


class read_writeTest(unittest.TestCase):
    """Test the reading and writing of field constructs from/to disk."""

    filename = filename

    zarr2 = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "example_field_0.zarr2"
    )

    zarr3 = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "example_field_0.zarr3"
    )

    f0 = cfdm.example_field(0)
    f1 = cfdm.example_field(1)

    string_filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "string_char.nc"
    )

    netcdf3_fmts = [
        "NETCDF3_CLASSIC",
        "NETCDF3_64BIT",
        "NETCDF3_64BIT_OFFSET",
        "NETCDF3_64BIT_DATA",
    ]
    netcdf4_fmts = ["NETCDF4", "NETCDF4_CLASSIC"]
    netcdf_fmts = netcdf3_fmts + netcdf4_fmts

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

    def test_read_write_zarr_1(self):
        """Test the writing of a named netCDF file."""
        i = 0
        for f in cfdm.example_fields(0, 1, 2, 3):
            print ('\n\n==================================', i)
            print(f)
            tmp1 = 'tmp.zarr'
            cfdm.write(f, tmp1, fmt='ZARR3')
            g = cfdm.read(tmp1, verbose=1)
            self.assertEqual(len(g) , 1)
            g = g[0]
            print(g)
            
            self.assertTrue(g.equals(f, verbose=1))

            print ('\n\n eq1 done\n\n')
            # Check that the Zarr and netCDF4 encoding contain the
            # same information
            tmpfile = 'delme.nc'
            cfdm.write(f, tmpfile, fmt='NETCDF4')
            n = cfdm.read(tmpfile)[0]
            self.assertTrue(g.equals(n))

            i += 1
if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
