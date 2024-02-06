import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

import netCDF4
import numpy as np

import cfdm

faulthandler.enable()  # to debug seg faults and timeouts

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_NetCDFIndexer.nc", dir=os.getcwd())[1]
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

netCDF_backends = ("netCDF4", "h5netcdf")


class NetCDFIndexerTest(unittest.TestCase):
    """Test the masking and scaling of netCDF data."""

    def test_NetCDFIndexer_shape(self):
        """Test NetCDFIndexer shape."""
        n = np.ma.arange(9)
        x = cfdm.NetCDFIndexer(n)
        self.assertEqual(x.shape, n.shape)

    def test_NetCDFIndexer_mask(self):
        """Test NetCDFIndexer for CF masking."""
        f0 = cfdm.example_field(0)
        f0.del_property("missing_value", None)
        f0.del_property("_FillValue", None)
        fields = [f0.copy()]

        f0.data[1, :] = np.ma.masked
        fields.append(f0)

        f = f0.copy()
        f.set_property("missing_value", 999)
        fields.append(f)

        f = f0.copy()
        f.set_property("_FillValue", 999)
        fields.append(f)

        f = f0.copy()
        valid_min = f.array.min() * 1.1
        f.set_property("valid_min", valid_min)
        fields.append(f)

        f = f0.copy()
        valid_max = f.array.max() * 0.9
        f.set_property("valid_max", valid_max)
        fields.append(f)

        f = f0.copy()
        f.set_property("valid_range", [valid_min, valid_max])
        fields.append(f)

        cfdm.write(fields, tmpfile, warn_valid=False)

        # Check against netCDF4 with set_auto_maskandscale(True)
        nc = netCDF4.Dataset(tmpfile, "r")
        nc.set_auto_maskandscale(True)
        nc.set_always_mask(True)
        for backend in netCDF_backends:
            f = cfdm.read(tmpfile, netCDF_backend=backend)
            for g in f:
                ncvar = g.nc_get_variable()
                n = nc.variables[ncvar]
                na = n[...]
                self.assertTrue((g.array == na).all())
                self.assertTrue((g.data.mask.array == na.mask).all())

        nc.close()

    def test_NetCDFIndexer_scale(self):
        """Test NetCDFIndexer for CF scaling."""
        f = cfdm.example_field(0)

        array = np.ma.arange(40, dtype="int32").reshape(f.shape)
        array[1, :] = np.ma.masked

        data = cfdm.Data(array, units=f.get_property("units"))
        f.set_data(data)
        scale_factor = 0.5
        add_offset = 10.0
        f.set_property("scale_factor", scale_factor)
        f.set_property("add_offset", add_offset)
        f.set_property("missing_value", 999)

        cfdm.write(f, tmpfile)

        # Check against netCDF4 with set_auto_maskandscale(True)
        nc = netCDF4.Dataset(tmpfile, "r")
        nc.set_auto_maskandscale(True)
        nc.set_always_mask(True)
        for backend in netCDF_backends:
            f = cfdm.read(tmpfile, netCDF_backend=backend)
            for g in f:
                ncvar = g.nc_get_variable()
                n = nc.variables[ncvar]
                na = n[...]
                self.assertTrue((g.array == na).all())
                self.assertTrue((g.data.mask.array == na.mask).all())

        nc.close()

    def test_NetCDFIndexer_numpy(self):
        """Test NetCDFIndexer for numpy."""
        array = np.ma.arange(9)
        x = cfdm.NetCDFIndexer(array)
        x = x[...]
        self.assertTrue((x == array).all())

        x = cfdm.NetCDFIndexer(
            array.copy(), attrs={"_FillValue": 4, "missing_value": (0, 8)}
        )
        x = x[...]
        array[[0, 4, 8]] = np.ma.masked
        self.assertTrue((x.mask == array.mask).all())
        self.assertTrue((x == array).all())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
