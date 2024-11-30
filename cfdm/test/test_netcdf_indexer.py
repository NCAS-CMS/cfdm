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
    tempfile.mkstemp("_test_netcdf_indexer.nc", dir=os.getcwd())[1]
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

netcdf_backends = ("netCDF4", "h5netcdf")


class netcdf_indexerTest(unittest.TestCase):
    """Test the masking and scaling of netCDF data."""

    f0 = cfdm.example_field(0)

    def test_netcdf_indexer_shape(self):
        """Test netcdf_indexer shape."""
        n = np.ma.arange(9)
        x = cfdm.netcdf_indexer(n)
        self.assertEqual(x.shape, n.shape)
        self.assertEqual(x.size, n.size)
        self.assertEqual(x.ndim, n.ndim)
        self.assertEqual(x.dtype, n.dtype)

    def test_netcdf_indexer_mask(self):
        """Test netcdf_indexer for masking."""
        f0 = self.f0.copy()
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
        for backend in netcdf_backends:
            f = cfdm.read(tmpfile, netcdf_backend=backend)
            for g in f:
                ncvar = g.nc_get_variable()
                n = nc.variables[ncvar]
                na = n[...]
                self.assertTrue((g.array == na).all())
                self.assertTrue((g.data.mask.array == na.mask).all())

        nc.close()

    def test_netcdf_indexer_unpack(self):
        """Test netcdf_indexer for unpacking."""
        f = self.f0.copy()

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
        for backend in netcdf_backends:
            f = cfdm.read(tmpfile, netcdf_backend=backend)
            for g in f:
                ncvar = g.nc_get_variable()
                n = nc.variables[ncvar]
                na = n[...]
                self.assertTrue((g.array == na).all())
                self.assertTrue((g.data.mask.array == na.mask).all())

        nc.close()

    def test_netcdf_indexer_numpy(self):
        """Test netcdf_indexer for numpy."""
        array = np.ma.arange(9)
        x = cfdm.netcdf_indexer(array)
        x = x[...]
        self.assertTrue((x == array).all())

        x = cfdm.netcdf_indexer(
            array.copy(), attributes={"_FillValue": 4, "missing_value": (0, 8)}
        )
        x = x[...]
        array[[0, 4, 8]] = np.ma.masked
        self.assertTrue((x.mask == array.mask).all())
        self.assertTrue((x == array).all())

    def test_netcdf_indexer_orthogonal_indexing(self):
        """Test netcdf_indexer for numpy orthogonal indexing."""
        array = np.ma.arange(120).reshape(2, 3, 4, 5)
        x = cfdm.netcdf_indexer(
            array, mask=False, unpack=False, orthogonal_indexing=True
        )

        y = x[..., [0, 2], :]
        a = array[..., [0, 2], :]
        self.assertTrue((y == a).all())

        y = x[1, ..., [0, 2], [0, 2, 3]]
        a = array[:, :, [0, 2], :]
        a = a[..., [0, 2, 3]]
        a = a[1, ...]
        self.assertTrue((y == a).all())

    def test_netcdf_indexer_non_orthogonal_indexing(self):
        """Test netcdf_indexer for numpy non-orthogonal indexing."""
        array = np.ma.arange(120).reshape(2, 3, 4, 5)
        x = cfdm.netcdf_indexer(array, mask=False, unpack=False)

        y = x[..., [0, 2], :]
        a = array[..., [0, 2], :]
        self.assertTrue((y == a).all())

        index = (Ellipsis, [0, 2], [2, 3])
        y = x[index]
        a = array[index]
        self.assertEqual(y.shape, a.shape)
        self.assertTrue((y == a).all())

        index = (1, Ellipsis, [0, 2], [2, 3])
        y = x[index]
        a = array[index]
        self.assertEqual(y.shape, a.shape)
        self.assertTrue((y == a).all())

    def test_netcdf_always_masked_array(self):
        """Test netcdf_indexer for numpy masked output."""
        array = np.ma.arange(9)
        x = cfdm.netcdf_indexer(array)
        self.assertFalse(np.ma.isMA(x[...]))
        x = cfdm.netcdf_indexer(array, always_masked_array=True)
        self.assertTrue(np.ma.isMA(x[...]))

    def test_netcdf_indexer_Ellipsis(self):
        """Test netcdf_indexer with Ellipsis."""
        n = np.arange(9)
        x = cfdm.netcdf_indexer(n)
        self.assertTrue((x[...] == n).all())

    def test_netcdf_indexer_index_shape(self):
        """Test netcdf_indexer shape."""
        x = cfdm.netcdf_indexer
        self.assertEqual(x.index_shape((slice(2, 5), [4]), (10, 20)), [3, 1])
        self.assertEqual(x.index_shape((slice(2, 5), 4), (10, 20)), [3])
        self.assertEqual(
            x.index_shape(([2, 3, 4], np.arange(1, 6)), (10, 20)), [3, 5]
        )

        self.assertEqual(
            x.index_shape((slice(None), [True, False, True]), (10, 3)), [10, 2]
        )

        index0 = np.arange(5)
        index0 = index0[index0 < 3]
        self.assertEqual(x.index_shape((index0, []), (10, 20)), [3, 0])

        self.assertEqual(
            x.index_shape((slice(1, 5, 3), [3]), (10, 20)), [2, 1]
        )
        self.assertEqual(x.index_shape((slice(5, 1, -2), 3), (10, 20)), [2])
        self.assertEqual(
            x.index_shape((slice(5, 1, 3), [3]), (10, 20)), [0, 1]
        )
        self.assertEqual(x.index_shape((slice(1, 5, -3), 3), (10, 20)), [0])


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
