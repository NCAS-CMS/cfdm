import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class NetCDFArrayTest(unittest.TestCase):
    """Unit test for the NetCDFArray class."""

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


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
