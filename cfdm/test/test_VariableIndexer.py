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
    tempfile.mkstemp("_test_VariableIndxer.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tempfile,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class VariableIndexerTest(unittest.TestCase):
    """Test the masking and scaling of netCDF data."""

    def test_mask(self):
        """Test CF masking."""
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

        cfdm.write(fields, tempfile, warn_valid=False)

        fh5 = cfdm.read(tempfile, netCDF_backend="h5netcdf")
        fnc = cfdm.read(tempfile, netCDF_backend="netCDF4")
        for h, n in zip(fh5, fnc):
            self.assertTrue(h.data.mask.equals(n.data.mask))

    def test_scale(self):
        """Test CF scaling."""
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

        cfdm.write(f, tempfile)
        x = cfdm.read(tempfile)[0]

        nc = netCDF4.Dataset(tempfile, "r")
        q = nc.variables["q"]
        q.set_auto_maskandscale(False)

        raw = (array - add_offset) / scale_factor
        raw[1, :] = 999
        raw = raw.astype(array.dtype)
        self.assertEqual(q.dtype, raw.dtype)
        self.assertTrue((q[...] == raw).all())
        nc.close()

        x = x.array
        self.assertTrue((x.mask == array.mask).all())
        self.assertTrue((x == array).all())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
