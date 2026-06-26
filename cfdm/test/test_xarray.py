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
            self.assertIn("Conventions", ds.attrs)
            str(ds)

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

    def test_Field_to_xarray_from_disk(self):
        """Test Field.to_xarray on datasets read from disk."""
        for dataset in (
            "example_field_0.nc",
            "example_field_0.zarr2",
            "example_field_0.zarr3",
            "gathered.nc",
            "DSG_timeSeries_contiguous.nc",
            "DSG_timeSeries_indexed.nc",
            "DSG_timeSeriesProfile_indexed_contiguous.nc",
            "parent.nc",
            "external.nc",
            "external_missing.nc",
            "combined.nc",
            "geometry_1.nc",
            "geometry_2.nc",
            "geometry_3.nc",
            "geometry_4.nc",
            "geometry_interior_ring.nc",
            "geometry_interior_ring_2.nc",
            "string_char.nc",
            "subsampled_2.nc",
            "ugrid_1.nc",
            "ugrid_2.nc",
            "ugrid_3.nc",
            "test_file.nc",
        ):
            for f in cfdm.read(dataset):
                ds = f.to_xarray()
                self.assertIsInstance(ds, xr.Dataset)
                str(ds)

    def test_Field_to_xarray_groups(self):
        """Test Field.to_xarray with groups."""
        f = cfdm.example_field(0)
        g = f.copy()

        ds = f.to_xarray()
        self.assertIsInstance(ds, xr.Dataset)

        f.nc_set_variable("/forecast/model/q2")
        ds = f.to_xarray()
        self.assertIsInstance(ds, xr.DataTree)
        self.assertIn("q2", ds["/forecast/model"])
        str(ds)

        # group=True
        ds = cfdm.write([f, g], fmt="XARRAY")
        self.assertIsInstance(ds, xr.DataTree)
        str(ds)

        self.assertIn("q", ds)
        self.assertIn("q2", ds["/forecast/model"])

        # group=False
        ds = f.to_xarray(group=False)
        self.assertIsInstance(ds, xr.Dataset)
        self.assertIn("q2", ds)
        str(ds)

        ds = cfdm.write([f, g], fmt="XARRAY", group=False)
        self.assertIsInstance(ds, xr.Dataset)
        str(ds)

        self.assertIn("q", ds)
        self.assertIn("q2", ds)

    def test_write_xarray_external(self):
        """Test cfdm.write with xarray and external file."""
        f = cfdm.example_field(0)
        with self.assertRaises(ValueError):
            cfdm.write(f, fmt="XARRAY", external="file.nc")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
