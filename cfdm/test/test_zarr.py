import atexit
import datetime
import faulthandler
import os
import shutil
import tempfile
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import zarr

import cfdm

warnings = False

# Set up temporary directories
tmpdirs = [
    tempfile.mkdtemp("_test_zarr.zarr", dir=os.getcwd()) for i in range(2)
]
[tmpdir1, tmpdir2] = tmpdirs

# Set up temporary files
tmpfiles = [
    tempfile.mkstemp("_test_zarr.nc", dir=os.getcwd())[1] for i in range(2)
]
[tmpfile1, tmpfile2] = tmpfiles


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


class read_writeTest(unittest.TestCase):
    """Test the reading and writing of field constructs from/to disk."""

    f0 = cfdm.example_field(0)

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

    def test_zarr_read_write_1(self):
        """Test Zarr read/write on example fields."""
        for i, f in enumerate(cfdm.example_fields()):
            if i in (8, 9, 10):
                # Can't write UGRID yet
                continue

            cfdm.write(f, tmpdir1, fmt="ZARR3")
            z = cfdm.read(tmpdir1)
            self.assertEqual(len(z), 1)
            z = z[0]
            self.assertTrue(z.equals(f))

            # Check that the Zarr and netCDF4 encodings are equivalent
            tmpfile1 = "delme.nc"
            cfdm.write(f, tmpfile1, fmt="NETCDF4")
            n = cfdm.read(tmpfile1)[0]
            self.assertTrue(z.equals(n))

    def test_zarr_read_write_2(self):
        """Test Zarr read/write on test netCDF files."""
        for filename in (
            "DSG_timeSeries_contiguous.nc",
            "DSG_timeSeries_indexed.nc",
            "DSG_timeSeriesProfile_indexed_contiguous.nc",
            "gathered.nc",
            "geometry_1.nc",
            "geometry_2.nc",
            "geometry_3.nc",
            "geometry_4.nc",
            "string_char.nc",
        ):
            n = cfdm.read(filename)
            cfdm.write(n, tmpdir1, fmt="ZARR3")
            z = cfdm.read(tmpdir1)
            self.assertEqual(len(z), len(n))
            for a, b in zip(z, n):
                self.assertTrue(a.equals(b))

    def test_zarr_read_write_shards(self):
        """Test Zarr read/write with shards."""
        f = self.f0.copy()
        f.data.nc_set_dataset_chunksizes([2, 3])

        cfdm.write(f, tmpdir1, fmt="ZARR3")
        z = zarr.open(tmpdir1)
        self.assertEqual(z["q"].chunks, (2, 3))
        self.assertIsNone(z["q"].shards)

        # Make shards comprising 4 chunks
        cfdm.write(f, tmpdir1, fmt="ZARR3", dataset_shards=4)
        z = zarr.open(tmpdir1)
        self.assertEqual(z["q"].chunks, (2, 3))
        self.assertEqual(z["q"].shards, (4, 6))

        for shards in (4, [2, 2]):
            f.data.nc_set_dataset_shards(shards)
            cfdm.write(f, tmpdir1, fmt="ZARR3")
            z = zarr.open(tmpdir1)
            self.assertEqual(z["q"].chunks, (2, 3))
            self.assertEqual(z["q"].shards, (4, 6))

    def test_zarr_read_write_CFA(self):
        """Test CF aggreagtion in Zarr."""
        f = self.f0
        cfdm.write(f, tmpdir1, fmt="ZARR3")
        cfdm.write(f, tmpfile1, fmt="NETCDF4")

        z = cfdm.read(tmpdir1, cfa_write="field")[0]
        n = cfdm.read(tmpfile1, cfa_write="field")[0]

        self.assertTrue(z.equals(f))
        self.assertTrue(z.equals(n))

        cfdm.write(z, tmpdir2, fmt="ZARR3", cfa="field")
        cfdm.write(n, tmpfile2, fmt="NETCDF4", cfa="field")

        z = cfdm.read(tmpdir2)[0]
        n = cfdm.read(tmpfile2)[0]

        self.assertTrue(z.equals(f))
        self.assertTrue(z.equals(n))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
