import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import numpy as np
from dask.base import tokenize

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_XnetcdfArray.nc", dir=os.getcwd())[1]
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


class XnetcdfArrayTest(unittest.TestCase):
    """Unit test for the XnetcdfArray class."""

    f0 = cfdm.example_field(0)

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

    def test_XnetcdfArray_get_address(self):
        """Test XnetcdfArray.get_address."""
        a = cfdm.XnetcdfArray(address="tas")
        self.assertEqual(a.get_address(), "tas")

        a = cfdm.XnetcdfArray()
        self.assertIsNone(a.get_address(default=None))

    def test_XnetcdfArray_get_filename(self):
        """Test XnetcdfArray.get_filename."""
        a = cfdm.XnetcdfArray("/data1/file1")
        self.assertEqual(a.get_filename(), "/data1/file1")

        a = cfdm.XnetcdfArray()
        self.assertIsNone(a.get_filename(default=None))

    def test_XnetcdfArray_mask(self):
        """Test XnetcdfArray masking."""
        f = self.f0
        f.data[0] = np.ma.masked
        cfdm.write(f, tmpfile)
        array = f.array

        n = cfdm.XnetcdfArray(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertTrue(n.get_mask())
        n = np.asanyarray(n[...])
        self.assertTrue((array.mask == n.mask).all())

        n = cfdm.XnetcdfArray(
            tmpfile, f.nc_get_variable(), shape=f.shape, mask=False
        )
        self.assertFalse(n.get_mask())
        n = np.asanyarray(n[...])
        self.assertEqual(np.ma.count(n), n.size)

    def test_XnetcdfArray_unpack(self):
        """Test XnetcdfArray unpacking."""
        add_offset = 10.0
        scale_factor = 3.14

        f = self.f0.copy()
        f.data[0] = np.ma.masked
        array0 = f.array
        array1 = (array0 - add_offset) / scale_factor

        f.set_property("add_offset", add_offset)
        f.set_property("scale_factor", scale_factor)
        cfdm.write(f, tmpfile)

        n = cfdm.XnetcdfArray(tmpfile, f.nc_get_variable(), shape=f.shape)
        self.assertTrue(n.get_unpack())
        n = np.asanyarray(n[...])

        self.assertTrue((n.mask == array0.mask).all())
        self.assertTrue(np.ma.allclose(n, array0))

        n = cfdm.XnetcdfArray(
            tmpfile, f.nc_get_variable(), shape=f.shape, unpack=False
        )
        self.assertFalse(n.get_unpack())
        n = np.asanyarray(n[...])
        self.assertTrue((n.mask == array1.mask).all())
        self.assertTrue((n == array1).all())

    def test_XnetcdfArray_get_attributes(self):
        """Test XnetcdfArray get_attributes."""
        f = self.f0
        cfdm.write(f, tmpfile)
        n = cfdm.XnetcdfArray(tmpfile, f.nc_get_variable(), shape=f.shape)
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

    def test_XnetcdfArray_file_directory(self):
        """Test XnetcdfArray.file_directory."""
        a = cfdm.XnetcdfArray("/data1/file1")
        self.assertEqual(a.file_directory(), "/data1")

        a = cfdm.XnetcdfArray()
        self.assertIsNone(a.file_directory(default=None))

    def test_XnetcdfArray__dask_tokenize__(self):
        """Test XnetcdfArray.__dask_tokenize__"""
        a = cfdm.XnetcdfArray("/data1/file1", "tas", shape=(12, 2), mask=False)
        self.assertEqual(tokenize(a), tokenize(a.copy()))

        b = cfdm.XnetcdfArray("/home/file2", "tas", shape=(12, 2))
        self.assertNotEqual(tokenize(a), tokenize(b))

    def test_XnetcdfArray_shape(self):
        """Test XnetcdfArray.shape."""
        shape = (12, 73, 96)
        a = cfdm.XnetcdfArray("/home/file2", "tas", shape=shape)
        self.assertEqual(a.shape, shape)
        self.assertEqual(a.original_shape, shape)
        a = a[::2]
        self.assertEqual(a.shape, (shape[0] // 2,) + shape[1:])
        self.assertEqual(a.original_shape, shape)

    def test_XnetcdfArray_index(self):
        """Test XnetcdfArray.index."""
        shape = (12, 73, 96)
        a = cfdm.XnetcdfArray("/home/file2", "tas", shape=shape)
        self.assertEqual(list(a.index()), [slice(0, n, 1) for n in shape])
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

        # New dimensions
        a = cfdm.XnetcdfArray("/home/file2", "tas", shape=shape)

        b = a[:2, None, ...]
        self.assertEqual(
            b.index(), (slice(0, 2, 1), None, slice(0, 73, 1), slice(0, 96, 1))
        )
        self.assertEqual(b.shape, (2, 1, 73, 96))
        self.assertEqual(b.reference_shape, (12, 1, 73, 96))

        b = b[...]
        self.assertEqual(
            b.index(), (slice(0, 2, 1), None, slice(0, 73, 1), slice(0, 96, 1))
        )
        self.assertEqual(b.shape, (2, 1, 73, 96))
        self.assertEqual(b.reference_shape, (12, 1, 73, 96))

        b = b[..., :4]
        self.assertEqual(
            b.index(), (slice(0, 2, 1), None, slice(0, 73, 1), slice(0, 4, 1))
        )
        self.assertEqual(b.shape, (2, 1, 73, 4))
        self.assertEqual(b.reference_shape, (12, 1, 73, 96))

        b = b[..., None, :]
        self.assertEqual(
            b.index(),
            (slice(0, 2, 1), None, slice(0, 73, 1), None, slice(0, 4, 1)),
        )
        self.assertEqual(b.shape, (2, 1, 73, 1, 4))
        self.assertEqual(b.reference_shape, (12, 1, 73, 1, 96))

        b = b[..., None]
        self.assertEqual(
            b.index(),
            (
                slice(0, 2, 1),
                None,
                slice(0, 73, 1),
                None,
                slice(0, 4, 1),
                None,
            ),
        )
        self.assertEqual(b.shape, (2, 1, 73, 1, 4, 1))
        self.assertEqual(b.reference_shape, (12, 1, 73, 1, 96, 1))

        with self.assertRaises(IndexError):
            # index 4 is out of bounds for axis 5 with size 1
            b[..., 4]

        b = b[:, 0, :, -1, :, 0]
        self.assertEqual(
            b.index(), (slice(0, 2, 1), slice(0, 73, 1), slice(0, 4, 1))
        )
        self.assertEqual(b.shape, (2, 73, 4))
        self.assertEqual(b.original_shape, shape)
        self.assertEqual(b.reference_shape, shape)

    def test_XnetcdfArray_replace_directory(self):
        """Test XnetcdfArray.replace_directory."""
        cwd = os.getcwd()

        n = cfdm.XnetcdfArray("basename.nc")

        m = n.replace_directory()
        self.assertEqual(m.get_filename(), "basename.nc")
        m = n.replace_directory(new="data")
        self.assertEqual(m.get_filename(), "data/basename.nc")
        m = n.replace_directory(normalise=True)
        self.assertEqual(m.get_filename(), os.path.join(cwd, "basename.nc"))

        n = cfdm.XnetcdfArray("data/basename.nc")

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

        n = cfdm.XnetcdfArray("path/basename.nc")
        m = n.replace_directory("path", "../new_path")
        self.assertEqual(m.get_filename(), "../new_path/basename.nc")

        n = cfdm.XnetcdfArray("/data/../new_path/basename.nc")
        m = n.replace_directory("/new_path/", normalise=True)
        self.assertEqual(m.get_filename(), "basename.nc")

        n = cfdm.XnetcdfArray("/data/basename.nc")
        m = n.replace_directory(new="/home")
        self.assertEqual(m.get_filename(), "/home/data/basename.nc")

        n = cfdm.XnetcdfArray("/data/basename.nc")
        m = n.replace_directory(new="/home/")
        self.assertEqual(m.get_filename(), "/home/data/basename.nc")
        m = n.replace_directory(old="/data")
        self.assertEqual(m.get_filename(), "basename.nc")

    def test_XnetcdfArray_concatenate(self):
        """Test np.concatenate on XnetcdfArray objects."""
        f = self.f0
        f.data[0] = np.ma.masked
        cfdm.write(f, tmpfile)

        array = f.array
        c0 = np.ma.concatenate((array, array), axis=0)

        n = cfdm.XnetcdfArray(
            tmpfile, f.nc_get_variable(), shape=f.shape, dtype=f.dtype
        )

        c1 = np.concatenate((n, n), axis=0)
        self.assertTrue(np.ma.is_masked(c1))

        self.assertEqual(c0.shape, c1.shape)
        self.assertTrue((c0.mask == c1.mask).all())
        self.assertTrue((c0 == c1).all())

    def test_XnetcdfArray_astype(self):
        """Test XnetcdfArray.astype."""
        f = self.f0
        cfdm.write(f, tmpfile)

        n = cfdm.XnetcdfArray(
            tmpfile, f.nc_get_variable(), shape=f.shape, dtype=f.dtype
        )
        self.assertNotEqual(n.dtype, np.dtype("int32"))

        a = n.astype("int32")
        self.assertIsInstance(a, np.ndarray)
        self.assertEqual(a.dtype, np.dtype("int32"))
        self.assertTrue((a == f.array.astype("int32")).all())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
