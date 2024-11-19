import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest
from urllib.parse import urlparse

faulthandler.enable()  # to debug seg faults and timeouts

import numpy as np
from dask.base import tokenize

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_netCDF.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tmpfile,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class NetCDF4ArrayTest(unittest.TestCase):
    """Unit test for the NetCDF4Array class."""

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

    def test_NetCDF4Array_get_addresses(self):
        """Test NetCDF4Array.get_addresses."""
        a = cfdm.NetCDF4Array(address="tas")
        self.assertEqual(a.get_addresses(), ("tas",))

    def test_NetCDF4Array_get_address(self):
        """Test NetCDF4Array.get_address."""
        a = cfdm.NetCDF4Array(address="tas")
        self.assertEqual(a.get_address(), "tas")

        a = cfdm.NetCDF4Array()
        self.assertIsNone(a.get_address(default=None))

    def test_NetCDF4Array_get_filenames(self):
        """Test NetCDF4Array.get_filenames."""
        a = cfdm.NetCDF4Array("/data1/file1")
        self.assertEqual(a.get_filenames(), ("/data1/file1",))

        a = cfdm.NetCDF4Array()
        self.assertEqual(a.get_filenames(), ())

    def test_NetCDF4Array_get_filename(self):
        """Test NetCDF4Array.get_filename."""
        a = cfdm.NetCDF4Array("/data1/file1")
        self.assertEqual(a.get_filename(), "/data1/file1")

        a = cfdm.NetCDF4Array()
        self.assertIsNone(a.get_filename(default=None))

    def test_NetCDF4Array_mask(self):
        """Test NetCDF4Array masking."""
        f = cfdm.example_field(0)
        f.data[0] = np.ma.masked
        cfdm.write(f, tmpfile)
        array = f.array

        n = cfdm.NetCDF4Array(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertTrue(n.get_mask())
        n = np.asanyarray(n[...])
        self.assertTrue((array.mask == n.mask).all())

        n = cfdm.NetCDF4Array(
            tmpfile, f.nc_get_variable(), shape=f.shape, mask=False
        )
        self.assertFalse(n.get_mask())
        n = np.asanyarray(n[...])
        self.assertEqual(np.ma.count(n), n.size)

    def test_NetCDF4Array_unpack(self):
        """Test NetCDF4Array unpacking."""
        add_offset = 10.0
        scale_factor = 3.14

        f = cfdm.example_field(0)
        f.data[0] = np.ma.masked
        array0 = f.array
        array1 = (array0 - add_offset) / scale_factor

        f.set_property("add_offset", add_offset)
        f.set_property("scale_factor", scale_factor)
        cfdm.write(f, tmpfile)

        n = cfdm.NetCDF4Array(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertTrue(n.get_unpack())
        n = np.asanyarray(n[...])
        self.assertTrue((n.mask == array0.mask).all())
        self.assertTrue(np.ma.allclose(n, array0))

        n = cfdm.NetCDF4Array(
            tmpfile, f.nc_get_variable(), shape=f.shape, unpack=False
        )
        self.assertFalse(n.get_unpack())
        n = np.asanyarray(n[...])
        self.assertTrue((n.mask == array1.mask).all())
        self.assertTrue((n == array1).all())

    def test_NetCDF4Array_get_storage_options(self):
        """Test NetCDF4Array get_storage_options."""
        n = cfdm.NetCDF4Array(filename="filename.nc")
        self.assertEqual(n.get_storage_options(), {})

        n = cfdm.NetCDF4Array(
            filename="filename.nc", storage_options={"anon": True}
        )
        self.assertEqual(n.get_storage_options(), {"anon": True})

        n = cfdm.NetCDF4Array(filename="s3://store/filename.nc")
        self.assertEqual(
            n.get_storage_options(), {"endpoint_url": "https://store"}
        )
        self.assertEqual(n.get_storage_options(create_endpoint_url=False), {})

        n = cfdm.NetCDF4Array(
            filename="s3://store/filename.nc", storage_options={"anon": True}
        )
        self.assertEqual(
            n.get_storage_options(),
            {"anon": True, "endpoint_url": "https://store"},
        )
        self.assertEqual(
            n.get_storage_options(create_endpoint_url=False), {"anon": True}
        )
        other_file = "s3://other/file.nc"
        self.assertEqual(
            n.get_storage_options(filename=other_file),
            {"anon": True, "endpoint_url": "https://other"},
        )
        self.assertEqual(
            n.get_storage_options(parsed_filename=urlparse(other_file)),
            {"anon": True, "endpoint_url": "https://other"},
        )

        n = cfdm.NetCDF4Array(
            filename="s3://store/filename.nc",
            storage_options={"anon": True, "endpoint_url": None},
        )
        self.assertEqual(
            n.get_storage_options(),
            {"anon": True, "endpoint_url": None},
        )

    def test_NetCDF4Array_get_attributes(self):
        """Test NetCDF4Array get_attributes."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile)
        n = cfdm.NetCDF4Array(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertEqual(n.get_attributes(), {})

        # Set attributes via indexing
        n = n[...]
        _ = np.asanyarray(n)
        self.assertEqual(
            n.get_attributes(),
            {
                "cell_methods": "area: mean",
                "coordinates": "time",
                "project": "research",
                "standard_name": "specific_humidity",
                "units": "1",
            },
        )

    def test_NetCDF4Array_file_directory(self):
        a = cfdm.NetCDF4Array("/data1/file1")
        self.assertEqual(a.file_directory(), "/data1")

        a = cfdm.NetCDF4Array()
        self.assertIsNone(a.file_directory(default=None))

    def test_NetCDF4Array__dask_tokenize__(self):
        a = cfdm.NetCDF4Array("/data1/file1", "tas", shape=(12, 2), mask=False)
        self.assertEqual(tokenize(a), tokenize(a.copy()))

        b = cfdm.NetCDF4Array("/home/file2", "tas", shape=(12, 2))
        self.assertNotEqual(tokenize(a), tokenize(b))

    def test_NetCDF4Array_shape(self):
        shape = (12, 73, 96)
        a = cfdm.NetCDF4Array("/home/file2", "tas", shape=shape)
        self.assertEqual(a.shape, shape)
        self.assertEqual(a.original_shape, shape)
        a = a[::2]
        self.assertEqual(a.shape, (shape[0] // 2,) + shape[1:])
        self.assertEqual(a.original_shape, shape)

    def test_NetCDF4Array_index(self):
        shape = (12, 73, 96)
        a = cfdm.NetCDF4Array("/home/file2", "tas", shape=shape)
        self.assertEqual(
            a.index(),
            (
                slice(
                    None,
                ),
            )
            * len(shape),
        )
        a = a[8:7:-1, 10:19:3, [15, 1, 4, 12]]
        a = a[[0], [True, False, True], ::-2]
        self.assertEqual(a.shape, (1, 2, 2))
        self.assertEqual(
            a.index(),
            (slice(8, 9, None), slice(10, 17, 6), slice(12, -1, -11)),
        )

        index = a.index(conform=False)
        self.assertTrue((index[0] == [8]).all())
        self.assertTrue((index[1] == [10, 16]).all())
        self.assertTrue((index[2] == [12, 1]).all())

    def test_NetCDF4Array_replace_directory(self):
        """Test NetCDF4Array.replace_directory."""
        cwd = os.getcwd()

        n = cfdm.NetCDF4Array("basename.nc")

        m = n.replace_directory()
        self.assertEqual(m.get_filename(), "basename.nc")
        m = n.replace_directory(new="data")
        self.assertEqual(m.get_filename(), "data/basename.nc")
        m = n.replace_directory(normalise=True)
        self.assertEqual(m.get_filename(), os.path.join(cwd, "basename.nc"))

        n = cfdm.NetCDF4Array("data/basename.nc")

        m = n.replace_directory()
        self.assertEqual(m.get_filename(), "data/basename.nc")
        m = n.replace_directory(new="/home")
        self.assertEqual(m.get_filename(), "/home/data/basename.nc")
        m = n.replace_directory(old="data")
        self.assertEqual(m.get_filename(), "basename.nc")
        m = n.replace_directory(old="data", new="home")
        self.assertEqual(m.get_filename(), "home/basename.nc")
        m = n.replace_directory(normalise=True)
        self.assertEqual(
            m.get_filename(), os.path.join(cwd, "data/basename.nc")
        )
        m = n.replace_directory(old=cwd, new="new", normalise=True)
        self.assertEqual(
            m.get_filename(), os.path.join(cwd, "new/data/basename.nc")
        )


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
