import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest
from urllib.parse import urlparse

faulthandler.enable()  # to debug seg faults and timeouts

import numpy as np

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
        """Test `NetCDF4Array.get_addresses`"""
        a = cfdm.NetCDF4Array(address="tas")
        self.assertEqual(a.get_addresses(), ("tas",))

        a = cfdm.NetCDF4Array(address=("tas1", "tas1"))
        self.assertEqual(a.get_addresses(), ("tas1", "tas1"))

        a = cfdm.NetCDF4Array()
        self.assertEqual(a.get_addresses(), ())

    def test_NetCDF4Array_get_filenames(self):
        """Test `NetCDF4Array.get_filenames`"""
        a = cfdm.NetCDF4Array("/data1/file1")
        self.assertEqual(a.get_filenames(), ("/data1/file1",))

        a = cfdm.NetCDF4Array(("/data1/file1",))
        self.assertEqual(a.get_filenames(), ("/data1/file1",))

        a = cfdm.NetCDF4Array(("/data1/file1", "/data2/file2"))
        self.assertEqual(a.get_filenames(), ("/data1/file1", "/data2/file2"))

        a = cfdm.NetCDF4Array()
        self.assertEqual(a.get_filenames(), ())

    def test_NetCDF4Array_mask(self):
        """Test NetCDF4Array masking."""
        f = cfdm.example_field(0)
        f.data[0] = np.ma.masked
        cfdm.write(f, tmpfile)
        array = f.array

        n = cfdm.NetCDF4Array(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertTrue(n.get_mask())
        n = n[...]
        self.assertTrue((array.mask == n.mask).all())

        n = cfdm.NetCDF4Array(
            tmpfile, f.nc_get_variable(), shape=f.shape, mask=False
        )
        self.assertFalse(n.get_mask())
        n = n[...]
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
        n = n[...]
        self.assertTrue((n.mask == array0.mask).all())
        self.assertTrue(np.ma.allclose(n, array0))

        n = cfdm.NetCDF4Array(
            tmpfile, f.nc_get_variable(), shape=f.shape, unpack=False
        )
        self.assertFalse(n.get_unpack())
        n = n[...]
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
        self.assertIsNone(n.get_attributes(None))

        with self.assertRaises(ValueError):
            n.get_attributes()

        # Set attributes via indexing
        _ = n[...]
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


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
