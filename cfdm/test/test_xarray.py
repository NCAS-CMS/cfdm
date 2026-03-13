import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import xarray as xr

import cfdm


class xarrayTest(unittest.TestCase):
    """Unit test for converting to xarray."""

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

    def test_Field_to_xarray(self):
        """Test Field.to_xarray."""
        fields = cfdm.example_fields()

        # Write each field to a different xarray dataset
        for f in fields:
            ds = f.to_xarray()
            self.assertIsInstance(ds, xr.Dataset)
            str(ds)
            self.assertIn("Conventions", ds.attrs)

        # Write all fields to one xarray dataset
        ds = cfdm.write(fields, fmt="XARRAY")
        self.assertIsInstance(ds, xr.Dataset)
        str(ds)

    def test_Domain_to_xarray(self):
        """Test Domain.to_xarray."""
        domains = [f.domain for f in cfdm.example_fields()]

        # Write each domain to a different xarray dataset
        for d in domains:
            ds = d.to_xarray()
            self.assertIsInstance(ds, xr.Dataset)
            str(ds)

        # Write all domains to one xarray dataset
        ds = cfdm.write(domains, fmt="XARRAY")
        self.assertIsInstance(ds, xr.Dataset)
        str(ds)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
