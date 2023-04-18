import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

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


class NetCDFTest(unittest.TestCase):
    """Unit test for the NetCDF class."""

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

    def test_NetCDFArray_get_addresses(self):
        """Test `NetCDFArray.get_addresses`"""
        a = cfdm.NetCDFArray(address="tas")
        self.assertEqual(a.get_addresses(), ("tas",))

        a = cfdm.NetCDFArray(address=("tas1", "tas1"))
        self.assertEqual(a.get_addresses(), ("tas1", "tas1"))

        a = cfdm.NetCDFArray()
        self.assertEqual(a.get_addresses(), ())

    def test_NetCDFArray_get_filenames(self):
        """Test `NetCDFArray.get_filenames`"""
        a = cfdm.NetCDFArray("/data1/file1")
        self.assertEqual(a.get_filenames(), ("/data1/file1",))

        a = cfdm.NetCDFArray(("/data1/file1",))
        self.assertEqual(a.get_filenames(), ("/data1/file1",))

        a = cfdm.NetCDFArray(("/data1/file1", "/data2/file2"))
        self.assertEqual(a.get_filenames(), ("/data1/file1", "/data2/file2"))

        a = cfdm.NetCDFArray()
        self.assertEqual(a.get_filenames(), ())

    def test_NetCDFArray_get_missing_values(self):
        """Test NetCDFArray.get_missing_values."""
        f = cfdm.example_field(0)

        f.set_property("missing_value", -999)
        f.set_property("_FillValue", -3)
        f.set_property("valid_range", [-111, 222])
        cfdm.write(f, tmpfile)

        g = cfdm.read(tmpfile)[0]
        self.assertEqual(
            g.data.source().get_missing_values(),
            {
                "missing_value": -999.0,
                "_FillValue": -3,
                "valid_range": (-111, 222),
            },
        )

        c = g.coordinate("latitude")
        self.assertEqual(c.data.source().get_missing_values(), {})

        a = cfdm.NetCDFArray("file.nc", "ncvar")
        self.assertIsNone(a.get_missing_values())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
