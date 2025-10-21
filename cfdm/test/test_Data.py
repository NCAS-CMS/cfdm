import atexit
import datetime
import faulthandler
import itertools
import os
import tempfile
import unittest
import warnings

import cftime
import dask.array as da
import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm
from cfdm.functions import DeprecationError

# To facilitate the testing of logging outputs (see comment tag
# 'Logging note')
logger = cfdm.logging.getLogger(__name__)


n_tmpfiles = 2
tmpfiles = [
    tempfile.mkstemp("_test_Data.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
file_A, file_B = tmpfiles


def _remove_tmpfiles():
    """Try to remove defined temporary files by deleting their paths."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


def axis_combinations(ndim):
    """Create axes permutations for `test_Data_flatten`"""
    return [
        axes
        for n in range(1, ndim + 1)
        for axes in itertools.permutations(range(ndim), n)
    ]


class DataTest(unittest.TestCase):
    """Unit test for the Data class."""

    f0 = cfdm.example_field(0)

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        # cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

        expected_warning_msgs = [
            "divide by zero encountered in " + np_method
            for np_method in (
                "arctanh",
                "log",
                "double_scalars",
            )
        ] + [
            "invalid value encountered in " + np_method
            for np_method in (
                "arcsin",
                "arccos",
                "arctanh",
                "arccosh",
                "log",
                "sqrt",
                "double_scalars",
                "true_divide",
            )
        ]
        for expected_warning in expected_warning_msgs:
            warnings.filterwarnings(
                "ignore", category=RuntimeWarning, message=expected_warning
            )

    def test_Data__init__basic(self):
        """Test basic Data.__init__"""
        # Most __init__ parameters are covered by the various other
        # tests, so this is mainly to check trivial cases.
        cfdm.Data(0, "s")
        cfdm.Data(array=np.arange(5))
        cfdm.Data(source=self.filename)

        d = cfdm.Data()
        with self.assertRaises(ValueError):
            d.ndim

        with self.assertRaises(ValueError):
            d.get_filenames()

    def test_Data__init__no_args(self):
        """Test Data.__init__ with no arg."""
        # Most __init__ parameters are covered by the various other
        # tests, so this is mainly to check trivial cases.
        cfdm.Data()
        cfdm.Data(0, "s")
        cfdm.Data(array=np.arange(5))
        cfdm.Data(source=self.filename)

    def test_Data_any(self):
        """Test Data.any."""
        d = cfdm.Data([[0, 0, 0]])
        self.assertFalse(d.any())
        d[0, 0] = np.ma.masked
        self.assertFalse(d.any())
        d[0, 1] = 3
        self.assertTrue(d.any())
        d[...] = np.ma.masked
        self.assertFalse(d.any())

        d = cfdm.Data([[0, 2], [0, 4]])
        self.assertTrue(d.any())
        self.assertEqual(d.any(keepdims=False).shape, ())
        self.assertEqual(d.any(axis=()).shape, d.shape)
        self.assertTrue((d.any(axis=0).array == [False, True]).all())
        self.assertTrue((d.any(axis=1).array == [True, True]).all())
        self.assertEqual(d.any().Units, cfdm.Units())

        d[0] = cfdm.masked
        self.assertTrue((d.any(axis=0).array == [False, True]).all())
        self.assertTrue(
            (
                d.any(axis=1).array == np.ma.array([True, True], mask=[1, 0])
            ).all()
        )

        d[...] = cfdm.masked
        self.assertFalse(d.any())
        self.assertFalse(d.any(keepdims=False))

    def test_Data__repr__str(self):
        """Test all means of Data inspection."""
        for d in [
            cfdm.Data(9, units="km"),
            cfdm.Data([9], units="km"),
            cfdm.Data([[9]], units="km"),
            cfdm.Data([8, 9], units="km"),
            cfdm.Data([[8, 9]], units="km"),
            cfdm.Data([7, 8, 9], units="km"),
            cfdm.Data([[7, 8, 9]], units="km"),
            cfdm.Data([6, 7, 8, 9], units="km"),
            cfdm.Data([[6, 7, 8, 9]], units="km"),
            cfdm.Data([[6, 7], [8, 9]], units="km"),
            cfdm.Data([[6, 7, 8, 9], [6, 7, 8, 9]], units="km"),
        ]:
            _ = repr(d)
            _ = str(d)

        # Test when the data contains date-times with the first
        # element masked
        dt = np.ma.array([10, 20], mask=[True, False])
        d = cfdm.Data(dt, units="days since 2000-01-01")
        self.assertTrue(str(d) == "[--, 2000-01-21 00:00:00]")
        self.assertTrue(repr(d) == "<Data(2): [--, 2000-01-21 00:00:00]>")

        # Cached elements
        elements0 = (0, -1, 1)
        for array in ([1], [1, 2], [1, 2, 3]):
            elements = elements0[: len(array)]

            d = cfdm.Data(array)
            cache = d._get_cached_elements()
            for element in elements:
                self.assertNotIn(element, cache)

            self.assertEqual(str(d), str(array))
            cache = d._get_cached_elements()
            for element in elements:
                self.assertIn(element, cache)

            d[0] = 1
            cache = d._get_cached_elements()
            for element in elements:
                self.assertNotIn(element, cache)

            self.assertEqual(str(d), str(array))
            cache = d._get_cached_elements()
            for element in elements:
                self.assertIn(element, cache)

            self.assertEqual(str(d), str(array))
            cache = d._get_cached_elements()
            for element in elements:
                self.assertIn(element, cache)

        # Test when size > 3, i.e. second element is not there.
        d = cfdm.Data([1, 2, 3, 4])
        cache = d._get_cached_elements()
        for element in elements0:
            self.assertNotIn(element, cache)

        self.assertEqual(str(d), "[1, ..., 4]")
        cache = d._get_cached_elements()
        self.assertNotIn(1, cache)
        for element in elements0[:2]:
            self.assertIn(element, cache)

        d[0] = 1
        for element in elements0:
            self.assertNotIn(element, d._get_cached_elements())

    def test_Data__setitem__(self):
        """Test Data.__setitem__"""
        for hardmask in (False, True):
            a = np.ma.arange(90).reshape(9, 10)
            if hardmask:
                a.harden_mask()
            else:
                a.soften_mask()

            d = cfdm.Data(a.copy(), "metres", hardmask=hardmask, chunks=(3, 5))

            a[:, 1] = np.ma.masked
            d[:, 1] = cfdm.masked

            a[0, 2] = -6
            d[0, 2] = -6

            a[0:3, 1] = -1
            d[0:3, 1] = -1

            a[0:2, 3] = -1
            d[0:2, 3] = -1

            a[3, 4:6] = -2
            d[3, 4:6] = -2

            a[0:2, 1:4] = -3
            d[0:2, 1:4] = -3

            a[5:7, [3, 5, 6]] = -4
            d[5:7, [3, 5, 6]] = -4

            a[8, [8, 6, 5]] = -5
            d[8, [8, 6, 5]] = -5

            a[...] = -a
            d[...] = -d

            a[0] = a[2]
            d[0] = d[2]

            a[:, 0] = a[:, 2]
            d[:, 0] = d[:, 2]

            a[:, 1] = a[:, 3]
            d[:, 1] = a[:, 3:4]  # Note: a, not d

            d.__keepdims_indexing__ = False

            a[:, 2] = a[:, 4]
            d[:, 2] = d[:, 4]  # Note: d, not a

            self.assertTrue((d.array == a).all())
            self.assertTrue((d.array.mask == a.mask).all())

        # Multiple 1-d array indices
        a = np.arange(180).reshape(9, 2, 10)
        value = -1 - np.arange(16).reshape(4, 1, 4)

        d = cfdm.Data(a.copy())
        d[[2, 4, 6, 8], 0, [1, 2, 3, 4]] = value
        self.assertEqual(
            np.count_nonzero(np.ma.where(d.array < 0, 1, 0)), value.size
        )

        d = cfdm.Data(a.copy())
        d[[2, 4, 6, 8], :, [1, 2, 3, 4]] = value
        self.assertEqual(
            np.count_nonzero(np.ma.where(d.array < 0, 1, 0)),
            value.size * d.shape[1],
        )

        d = cfdm.Data(a.copy())
        d[[1, 2, 4, 5], 0, [5, 6, 7, -1]] = value
        self.assertEqual(
            np.count_nonzero(np.ma.where(d.array < 0, 1, 0)), value.size
        )

        d = cfdm.Data(a.copy())
        value = np.squeeze(value)
        d.__keepdims_indexing__ = False
        d[[2, 4, 6, 8], 0, [1, 2, 3, 4]] = value
        self.assertEqual(
            np.count_nonzero(np.ma.where(d.array < 0, 1, 0)), value.size
        )

        a = np.ma.arange(3000).reshape(50, 60)
        a.harden_mask()

        d = cfdm.Data(a.filled(), units="m")

        for n, (j, i) in enumerate(
            (
                (34, 23),
                (0, 0),
                (-1, -1),
                (slice(40, 50), slice(58, 60)),
                (Ellipsis, slice(None)),
                (slice(None), Ellipsis),
            )
        ):
            n = -n - 1
            for dvalue, avalue in (
                (n, n),
                (cfdm.masked, np.ma.masked),
                (n, n),
            ):
                d[j, i] = dvalue
                a[j, i] = avalue
                x = d.array
                self.assertTrue((x == a).all() in (True, np.ma.masked))
                m = np.ma.getmaskarray(x)
                self.assertTrue((m == np.ma.getmaskarray(a)).all())

        a = np.ma.arange(3000).reshape(50, 60)
        a.harden_mask()

        d = cfdm.Data(a.filled(), "m")

        (j, i) = (slice(0, 2), slice(0, 3))
        array = np.array([[1, 2, 6], [3, 4, 5]]) * -1

        for dvalue in (array, np.ma.masked_where(array < -2, array), array):
            d[j, i] = dvalue
            a[j, i] = dvalue
            x = d.array
            self.assertTrue((x == a).all() in (True, np.ma.masked))
            m = np.ma.getmaskarray(x)
            self.assertTrue((m == np.ma.getmaskarray(a)).all())

        # Scalar numeric array
        d = cfdm.Data(9, units="km")
        d[...] = cfdm.masked
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], np.ma.masked)

        # Multiple list indices, scalar value
        d = cfdm.Data(np.arange(40).reshape(5, 8), units="km")

        value = -1
        for indices in (
            ([0, 3, 4], [1, 6, 7]),
            ([0, 3, 4], [1, 7, 6]),
            ([0, 4, 3], [1, 6, 7]),
            ([0, 4, 3], [1, 7, 6]),
            ([4, 3, 0], [7, 6, 1]),
            ([4, 3, 0], [1, 6, 7]),
            ([0, 3, 4], [7, 6, 1]),
            ([0, 3, -1], [7, 6, 1]),
            ([0, 3, 4], [-1, 6, 1]),
            ([0, 3, -1], [-1, 6, 1]),
        ):
            d[indices] = value
            self.assertEqual((d.array == value).sum(), 9)
            value -= 1

        # Repeated list elements
        for indices in (
            ([0, 3, 3], [7, 6, 1]),
            ([3, 3, 0], [7, 6, 1]),
            ([0, 4, 3], [7, 6, 7]),
        ):
            d[indices] = value
            self.assertEqual((d.array == value).sum(), 6)
            value -= 1

        for indices in (
            ([3, 4, 3], [7, 6, 7]),
            ([3, 3, 4], [7, 7, 6]),
            ([4, 3, 3], [6, 7, 7]),
        ):
            d[indices] = value
            self.assertEqual((d.array == value).sum(), 4)
            value -= 1

        # Multiple list indices, array value
        a = np.arange(40).reshape(1, 5, 8)

        value = np.arange(9).reshape(3, 3) - 9

        for indices in (
            (slice(None), [0, 3, 4], [1, 6, 7]),
            (slice(None), [0, 3, 4], [1, 7, 6]),
            (slice(None), [0, 4, 3], [1, 6, 7]),
            (slice(None), [0, 4, 3], [1, 7, 6]),
            (slice(None), [4, 3, 0], [7, 6, 1]),
            (slice(None), [4, 3, 0], [1, 6, 7]),
            (slice(None), [0, 3, 4], [7, 6, 1]),
            (slice(None), [0, 3, -1], [7, 6, 1]),
            (slice(None), [0, 3, 4], [-1, 6, 1]),
            (slice(None), [0, 3, -1], [-1, 6, 1]),
        ):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 9)

        # Repeated list elements
        for indices in (
            (slice(None), [0, 3, 3], [7, 6, 1]),
            (slice(None), [0, 4, 3], [7, 6, 7]),
            (slice(None), [3, 3, 4], [1, 6, 7]),
            (slice(None), [0, 4, 3], [7, 7, 6]),
        ):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 6)

        for indices in (
            (slice(None), [3, 4, 3], [7, 6, 7]),
            (slice(None), [4, 3, 3], [6, 7, 7]),
            (slice(None), [3, 3, 4], [6, 7, 7]),
            (slice(None), [3, 3, 4], [7, 7, 6]),
            (slice(None), [4, 3, 3], [7, 7, 6]),
        ):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 4)

        # Multiple list indices, array value + broadcasting
        value = np.arange(3).reshape(1, 3) - 9

        for indices in ((slice(None), [0, 3, 4], [1, 6, 7]),):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 9)

        # Repeated list elements
        for indices in ((slice(None), [0, 3, 3], [7, 6, 1]),):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 6)

        for indices in ((slice(None), [4, 3, 3], [7, 7, 6]),):
            d = cfdm.Data(a.copy())
            d[indices] = value
            self.assertEqual((d.array < 0).sum(), 4)

    def test_Data_apply_masking(self):
        """Test Data.apply_masking."""
        a = np.ma.arange(12).reshape(3, 4)
        a[1, 1] = np.ma.masked

        d = cfdm.Data(a, units="m")

        self.assertTrue((a == d.array).all())
        self.assertTrue((a.mask == d.mask.array).all())

        b = a.copy()
        e = d.apply_masking()
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where(a == 0, np.ma.masked, a)
        e = d.apply_masking(fill_values=[0])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where((a == 0) | (a == 11), np.ma.masked, a)
        e = d.apply_masking(fill_values=[0, 11])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where(a < 3, np.ma.masked, a)
        e = d.apply_masking(valid_min=3)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where(a > 6, np.ma.masked, a)
        e = d.apply_masking(valid_max=6)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where((a < 2) | (a > 8), np.ma.masked, a)
        e = d.apply_masking(valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        d.set_fill_value(7)

        b = np.ma.where(a == 7, np.ma.masked, a)
        e = d.apply_masking(fill_values=True)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = np.ma.where((a == 7) | (a < 2) | (a > 8), np.ma.masked, a)
        e = d.apply_masking(fill_values=True, valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

    #    def test_Data_astype(self):
    #        a = np.array([1.5, 2, 2.5], dtype=float)
    #        d = cfdm.Data(a)
    #
    #        self.assertTrue(d.dtype == np.dtype(float))
    #        self.assertTrue(d.array.dtype == np.dtype(float))
    #        self.assertTrue((d.array == a).all())
    #
    #        d.astype('int32')
    #        self.assertTrue(d.dtype == np.dtype('int32'))
    #        self.assertTrue(d.array.dtype == np.dtype('int32'))
    #        self.assertTrue((d.array == [1, 2, 2]).all())
    #
    #        d = cfdm.Data(a)
    #        try:
    #            d.astype(np.dtype(int, casting='safe'))
    #            self.assertTrue(False)
    #        except TypeError:
    #            pass

    def test_Data_array(self):
        """Test Data.array."""
        # Scalar numeric array
        d = cfdm.Data(9, "km")
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertEqual(a, np.array(9))
        d[...] = cfdm.masked
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], np.ma.masked)

        # Non-scalar numeric array
        b = np.arange(24).reshape(2, 1, 3, 4)
        d = cfdm.Data(b, "km", fill_value=-123)
        a = d.array
        a[0, 0, 0, 0] = -999
        a2 = d.array
        self.assertTrue((a2 == b).all())
        self.assertFalse((a2 == a).all())

        # Fill value
        d[0, 0, 0, 0] = cfdm.masked
        self.assertEqual(d.array.fill_value, d.get_fill_value())

        # Date-time array
        d = cfdm.Data([["2000-12-3 12:00"]], "days since 2000-12-01", dt=True)
        self.assertEqual(d.array, 2.5)

        a = np.arange(12, dtype="int32").reshape(3, 4)

        d = cfdm.Data(a, units="km")

        b = np.array(d)

        self.assertEqual(b.dtype, np.dtype("int32"))
        self.assertEqual(a.shape, b.shape)
        self.assertTrue((a == b).all())

        b = np.array(d, dtype="float32")

        self.assertEqual(b.dtype, np.dtype("float32"))
        self.assertEqual(a.shape, b.shape)
        self.assertTrue((a == b).all())

        # Scalar numeric array
        d = cfdm.Data(9, units="km")
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertEqual(a, np.array(9))
        d[...] = cfdm.masked
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], np.ma.masked)

        # Non-scalar numeric array
        b = np.arange(10 * 15 * 19).reshape(10, 1, 15, 19)
        d = cfdm.Data(b, "km")
        a = d.array
        a[0, 0, 0, 0] = -999
        a2 = d.array
        self.assertEqual(a2[0, 0, 0, 0], 0)
        self.assertEqual(a2.shape, b.shape)
        self.assertTrue((a2 == b).all())
        self.assertFalse((a2 == a).all())

        # Date-time array
        d = cfdm.Data([["2000-12-3 12:00"]], "days since 2000-12-01", dt=True)
        self.assertEqual(d.array, 2.5)

    def test_Data_flatten(self):
        """Test Data.flatten."""
        ma = np.ma.arange(24).reshape(1, 2, 3, 4)
        ma[0, 1, 1, 2] = cfdm.masked
        ma[0, 0, 2, 1] = cfdm.masked

        d = cfdm.Data(ma.copy())
        self.assertTrue(d.equals(d.flatten([]), verbose=3))
        self.assertIsNone(d.flatten(inplace=True))

        d = cfdm.Data(ma.copy())

        b = ma.flatten()
        for axes in (None, list(range(d.ndim))):
            e = d.flatten(axes)
            self.assertEqual(e.ndim, 1)
            self.assertEqual(e.shape, b.shape)
            self.assertTrue(e.equals(cfdm.Data(b), verbose=3))

        for axes in axis_combinations(d.ndim):
            e = d.flatten(axes)

            if len(axes) <= 1:
                shape = d.shape
            else:
                shape = [n for i, n in enumerate(d.shape) if i not in axes]
                shape.insert(
                    sorted(axes)[0],
                    np.prod([n for i, n in enumerate(d.shape) if i in axes]),
                )

            self.assertEqual(e.shape, tuple(shape), axes)
            self.assertEqual(e.ndim, d.ndim - len(axes) + 1)
            self.assertEqual(e.size, d.size)

        for n in range(4):
            e = d.flatten(n)
            f = d.flatten([n])
            self.assertTrue(e.equals(f))

        with self.assertRaises(ValueError):
            d.flatten(99)

        d = cfdm.Data(9)
        self.assertTrue(d.equals(d.flatten()))
        self.assertTrue(d.equals(d.flatten([])))

        with self.assertRaises(ValueError):
            d.flatten(0)

    def test_Data_transpose(self):
        """Test Data.transpose."""
        a = np.arange(2 * 3 * 5).reshape(2, 1, 3, 5)
        d = cfdm.Data(a.copy())

        for indices in (list(range(a.ndim)), list(range(-a.ndim, 0))):
            for axes in itertools.permutations(indices):
                a = np.transpose(a, axes)
                d = d.transpose(axes)
                message = (
                    f"cfdm.Data.transpose({axes}) failed: d.shape={d.shape}, "
                    f"a.shape={a.shape}"
                )
                self.assertEqual(d.shape, a.shape, message)
                self.assertTrue((d.array == a).all(), message)

        with self.assertRaises(ValueError):
            d.transpose(axes=99)

        with self.assertRaises(ValueError):
            d.transpose(axes=[1, 2, 3, 4, 5])

        d = cfdm.Data(9)
        self.assertTrue(d.equals(d.transpose()))

        # Dataset chunks
        d = cfdm.Data(np.arange(12).reshape(1, 4, 3))
        d.nc_set_dataset_chunksizes((1, 4, 3))
        d.transpose(inplace=True)
        self.assertEqual(d.nc_dataset_chunksizes(), (3, 4, 1))

    def test_Data_unique(self):
        """Test Data.unique."""
        d = cfdm.Data([[4, 2, 1], [1, 2, 3]], units="metre")
        u = d.unique()
        self.assertEqual(u.shape, (4,))
        self.assertTrue(
            (u.array == cfdm.Data([1, 2, 3, 4], "metre").array).all()
        )

        d[1, -1] = cfdm.masked
        u = d.unique()
        self.assertEqual(u.shape, (4,))
        self.assertTrue(
            (u.array == np.ma.array([1, 2, 4, -99], mask=[0, 0, 0, 1])).all()
        )

        # Dataset chunks
        d = cfdm.Data(np.arange(12).reshape(1, 4, 3))
        d.nc_set_dataset_chunksizes((1, 4, 3))
        e = d.unique()
        self.assertIsNone(e.nc_dataset_chunksizes())

    def test_Data_equals(self):
        """Test Data.equals."""
        shape = 3, 4
        chunksize = 2, 6
        a = np.arange(12).reshape(*shape)

        d = cfdm.Data(a, "m", chunks=chunksize)
        self.assertTrue(d.equals(d))  # check equal to self
        self.assertTrue(d.equals(d.copy()))  # also do self-equality checks!

        # Different but equivalent datatype, which should *fail* the
        # equality test (i.e. equals return False) because we want
        # equals to check for strict equality, including equality of
        # data type.
        d2 = cfdm.Data(a.astype(np.float32), "m", chunks=chunksize)
        self.assertTrue(d2.equals(d2.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(d2.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different data types: float32 != int64" in log_msg
                    for log_msg in catch.output
                )
            )

        e = cfdm.Data(a, "s", chunks=chunksize)  # different units to d
        self.assertTrue(e.equals(e.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(e.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different Units (<Units: s>, <Units: m>)" in log_msg
                    for log_msg in catch.output
                )
            )

        f = cfdm.Data(np.arange(12), "m", chunks=(6,))  # different shape to d
        self.assertTrue(f.equals(f.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(f.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different shapes: (12,) != (3, 4)" in log_msg
                    for log_msg in catch.output
                )
            )

        g = cfdm.Data(
            np.ones(shape, dtype="int64"), "m", chunks=chunksize
        )  # different values
        self.assertTrue(g.equals(g.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(g.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )

        # Test NaN values
        d3 = cfdm.Data(a.astype(np.float64), "m", chunks=chunksize)
        h = cfdm.Data(np.full(shape, np.nan), "m", chunks=chunksize)
        # TODODASK: implement and test equal_nan kwarg to configure NaN eq.
        self.assertFalse(h.equals(h.copy()))
        with self.assertLogs(level=-1) as catch:
            # Compare to d3 not d since np.nan has dtype float64 (IEEE 754)
            self.assertFalse(h.equals(d3, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )

        # Test inf values
        i = cfdm.Data(np.full(shape, np.inf), "m", chunks=chunksize)
        self.assertTrue(i.equals(i.copy()))
        with self.assertLogs(level=-1) as catch:
            # np.inf is also of dtype float64 (see comment on NaN tests above)
            self.assertFalse(i.equals(d3, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(h.equals(i, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )

        # Test masked arrays
        #
        # 1. Example case where the masks differ only (data is
        #    identical)
        mask_test_chunksize = (2, 1)
        j1 = cfdm.Data(
            np.ma.array([1.0, 2.0, 3.0], mask=[1, 0, 0]),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(j1.equals(j1.copy()))
        j2 = cfdm.Data(
            np.ma.array([1.0, 2.0, 3.0], mask=[0, 1, 0]),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(j2.equals(j2.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(j1.equals(j2, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )
        # 2. Example case where the data differs only (masks are
        #    identical)
        j3 = cfdm.Data(
            np.ma.array([1.0, 2.0, 100.0], mask=[1, 0, 0]),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(j3.equals(j3.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(j1.equals(j3, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )

        # 3. Trivial case of data that is fully masked
        j4 = cfdm.Data(
            np.ma.masked_all(shape, dtype="int"), "m", chunks=chunksize
        )
        self.assertTrue(j4.equals(j4.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(j4.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )
        # 4. Case where all the unmasked data is 'allclose' to other
        #    data but the data is not 'allclose' to it where it is
        #    masked, i.e. the data on its own (namely without
        #    considering the mask) is not equal to the other data on
        #    its own (e.g. note the 0-th element in below examples).
        #    This differs to case (2): there data differs *only where
        #    unmasked*.  Note these *should* be considered equal
        #    inside cfdm.Data, and indeed np.ma.allclose and our own
        #    _da_ma_allclose methods also hold these to be 'allclose'.
        j5 = cfdm.Data(
            np.ma.array([1.0, 2.0, 3.0], mask=[1, 0, 0]),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(j5.equals(j5.copy()))
        j6 = cfdm.Data(
            np.ma.array([10.0, 2.0, 3.0], mask=[1, 0, 0]),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(j6.equals(j6.copy()))
        self.assertTrue(j5.equals(j6))

        # Test non-numeric dtype arrays
        sa1 = cfdm.Data(
            np.array(["one", "two", "three"], dtype="S5"), "m", chunks=(3,)
        )
        self.assertTrue(sa1.equals(sa1.copy()))
        sa2_data = np.array(["one", "two", "four"], dtype="S4")
        sa2 = cfdm.Data(sa2_data, "m", chunks=(3,))
        self.assertTrue(sa2.equals(sa2.copy()))
        # Unlike for numeric types, for string-like data as long as
        # the data is the same consider the arrays equal, even if the
        # dtype differs.
        sa3_data = sa2_data.astype("S5")
        sa3 = cfdm.Data(sa3_data, "m", chunks=mask_test_chunksize)
        self.assertTrue(sa2.equals(sa3, verbose=2))
        self.assertTrue(sa3.equals(sa3.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(sa1.equals(sa3, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )
        # ...including masked string arrays
        sa4 = cfdm.Data(
            np.ma.array(["one", "two", "three"], mask=[0, 0, 1], dtype="S5"),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(sa4.equals(sa4.copy()))
        sa5 = cfdm.Data(
            np.ma.array(["one", "two", "three"], mask=[0, 1, 0], dtype="S5"),
            "m",
            chunks=mask_test_chunksize,
        )
        self.assertTrue(sa5.equals(sa5.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(sa4.equals(sa5, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )

        # Test where inputs are scalars
        scalar_test_chunksize = (10,)
        s1 = cfdm.Data(1, chunks=scalar_test_chunksize)
        self.assertTrue(s1.equals(s1.copy()))
        s2 = cfdm.Data(10, chunks=scalar_test_chunksize)
        self.assertTrue(s2.equals(s2.copy()))
        s3 = cfdm.Data("a_string", chunks=scalar_test_chunksize)
        self.assertTrue(s3.equals(s3.copy()))
        # 1. both are scalars
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(s1.equals(s2, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values" in log_msg
                    for log_msg in catch.output
                )
            )
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(s1.equals(s3, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different data types: int64 != <U8" in log_msg
                    for log_msg in catch.output
                )
            )
        # 2. only one is a scalar
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(s1.equals(d, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different shapes: () != (3, 4)" in log_msg
                    for log_msg in catch.output
                )
            )

        # Test rtol and atol parameters
        tol_check_chunksize = 1, 1
        k1 = cfdm.Data(np.array([10.0, 20.0]), chunks=tol_check_chunksize)
        self.assertTrue(k1.equals(k1.copy()))
        k2 = cfdm.Data(np.array([10.01, 20.01]), chunks=tol_check_chunksize)
        self.assertTrue(k2.equals(k2.copy()))
        # Only one log check is sufficient here
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(k1.equals(k2, atol=0.005, rtol=0, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different array values (atol=0.005, rtol=0.0)"
                    in log_msg
                    for log_msg in catch.output
                )
            )
        self.assertTrue(k1.equals(k2, atol=0.02, rtol=0))
        self.assertFalse(k1.equals(k2, atol=0, rtol=0.0005))
        self.assertTrue(k1.equals(k2, atol=0, rtol=0.002))

        # Test ignore_fill_value parameter
        m1 = cfdm.Data(1, fill_value=1000, chunks=scalar_test_chunksize)
        self.assertTrue(m1.equals(m1.copy()))
        m2 = cfdm.Data(1, fill_value=2000, chunks=scalar_test_chunksize)
        self.assertTrue(m2.equals(m2.copy()))
        with self.assertLogs(level=-1) as catch:
            self.assertFalse(m1.equals(m2, verbose=2))
            self.assertTrue(
                any(
                    "Data: Different fill value: 1000 != 2000" in log_msg
                    for log_msg in catch.output
                )
            )
            self.assertTrue(m1.equals(m2, ignore_fill_value=True))

        # Test verbose parameter: 1/'INFO' level is behaviour change boundary
        for checks in [(1, False), (2, True)]:
            verbosity_level, expect_to_see_msg = checks
            with self.assertLogs(level=-1) as catch:
                # Logging note: want to assert in the former case (verbosity=1)
                # that nothing is logged, but need to use workaround to prevent
                # AssertionError on fact that nothing is logged here. When at
                # Python =>3.10 this can be replaced by 'assertNoLogs' method.
                logger.warning(
                    "Log warning to prevent test error on empty log."
                )

                self.assertFalse(d2.equals(d, verbose=verbosity_level))
                self.assertIs(
                    any(
                        "Data: Different data types: float32 != int64"
                        in log_msg
                        for log_msg in catch.output
                    ),
                    expect_to_see_msg,
                )

        # Test ignore_data_type parameter
        self.assertTrue(d2.equals(d, ignore_data_type=True))

        # Test all possible chunk combinations
        for j, i in itertools.product([1, 2], [1, 2, 3]):
            d = cfdm.Data(np.arange(6).reshape(2, 3), "m", chunks=(j, i))
            for j, i in itertools.product([1, 2], [1, 2, 3]):
                e = cfdm.Data(np.arange(6).reshape(2, 3), "m", chunks=(j, i))
                self.assertTrue(d.equals(e))

    def test_Data_max_min_sum_squeeze(self):
        """Test the max, min, sum and squeeze Data methods."""
        a = np.ma.arange(2 * 3 * 5).reshape(2, 1, 3, 5)
        a[0, 0, 0, 0] = np.ma.masked
        a[-1, -1, -1, -1] = np.ma.masked
        a[1, -1, 1, 3] = np.ma.masked
        d = cfdm.Data(a)

        b = a.max()
        x = d.max().squeeze()
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=0)
        x = d.max(axes=0).squeeze(0)
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=(0, 3))
        x = d.max(axes=[0, 3]).squeeze([0, 3])
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())
        self.assertTrue(d.max([0, 3]).equals(d.max([0, 3])))

        b = a.min()
        x = d.min().squeeze()
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min(axis=(0, 3))
        x = d.min(axes=[0, 3]).squeeze([0, 3])
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all(), (x.shape, b.shape))
        self.assertTrue(d.min([0, 3]).equals(d.min([0, 3])))

        b = a.sum()
        x = d.sum().squeeze()
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.sum(axis=(0, 3))
        x = d.sum(axes=[0, 3]).squeeze([0, 3])
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all(), (x.shape, b.shape))

        with self.assertRaises(ValueError):
            d.sum(axes=99)

        with self.assertRaises(ValueError):
            d.squeeze(axes=99)

        with self.assertRaises(ValueError):
            d.squeeze(axes=2)

        with self.assertRaises(ValueError):
            d.max(axes=99)

        with self.assertRaises(ValueError):
            d.min(axes=99)

        d = cfdm.Data(9)
        self.assertTrue(d.equals(d.squeeze()))

        with self.assertRaises(ValueError):
            d.sum(axes=0)

        with self.assertRaises(ValueError):
            d.squeeze(axes=0)

        with self.assertRaises(ValueError):
            d.min(axes=0)

        with self.assertRaises(ValueError):
            d.max(axes=0)

        # Dataset chunks
        d = cfdm.Data(np.arange(12).reshape(1, 4, 3))
        d.nc_set_dataset_chunksizes((1, 4, 3))
        e = d.squeeze()
        self.assertEqual(e.nc_dataset_chunksizes(), (4, 3))
        e = d.max(axes=1)
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 1, 3))
        e = d.min(axes=1)
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 1, 3))
        e = d.sum(axes=1)
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 1, 3))
        e = d.max(axes=1, squeeze=True)
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 3))
        e = d.sum(axes=1, squeeze=True)
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 3))

    def test_Data_dtype_mask(self):
        """Test the dtype and mask Data methods."""
        a = np.ma.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        d = cfdm.Data([[280, -99, -99, -99], [281, 279, 278, 279]])
        self.assertEqual(d.dtype, np.dtype(int))

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertTrue((d.array == a).all())
        self.assertEqual(d.mask.shape, a.mask.shape)
        self.assertTrue((d.mask.array == np.ma.getmaskarray(a)).all())

        a = np.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]], dtype=float
        )
        mask = np.ma.masked_all(a.shape).mask

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]], dtype=float
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertTrue((d.array == a).all())
        self.assertEqual(d.mask.shape, mask.shape)
        self.assertTrue((d.mask.array == np.ma.getmaskarray(a)).all())

    def test_Data_get_index(self):
        """Test Data.get_index."""
        f = cfdm.read("DSG_timeSeries_indexed.nc")[0]
        f = f.data
        d = cfdm.Data(cfdm.RaggedIndexedArray(source=f.source()))
        self.assertIsInstance(d.get_index(), cfdm.Index)

        d = cfdm.Data(9, "m")
        self.assertIsNone(d.get_index(None))
        with self.assertRaises(ValueError):
            d.get_index()

    def test_Data_get_list(self):
        """Test Data.get_list."""
        f = cfdm.read("gathered.nc")[0]
        f = f.data
        d = cfdm.Data(cfdm.GatheredArray(source=f.source()))
        self.assertIsInstance(d.get_list(), cfdm.List)

        d = cfdm.Data(9, "m")
        self.assertIsNone(d.get_list(None))
        with self.assertRaises(ValueError):
            d.get_list()

    def test_Data_get_count(self):
        """Test Data.get_count."""
        f = cfdm.read("DSG_timeSeries_contiguous.nc")[0]
        f = f.data
        d = cfdm.Data(cfdm.RaggedContiguousArray(source=f.source()))
        self.assertIsInstance(d.get_count(), cfdm.Count)

        d = cfdm.Data(9, "m")
        self.assertIsNone(d.get_count(None))
        with self.assertRaises(ValueError):
            d.get_count()

    def test_Data_filled(self):
        """Test Data.filled."""
        d = cfdm.Data([[1, 2, 3]])
        self.assertTrue((d.filled().array == [[1, 2, 3]]).all())

        d[0, 0] = cfdm.masked
        self.assertTrue(
            (d.filled().array == [[-9223372036854775806, 2, 3]]).all()
        )

        d.set_fill_value(-99)
        self.assertTrue((d.filled().array == [[-99, 2, 3]]).all())

        self.assertTrue((d.filled(1e10).array == [[1e10, 2, 3]]).all())

        d = cfdm.Data(["a", "b", "c"], mask=[1, 0, 0])
        self.assertTrue((d.filled().array == ["", "b", "c"]).all())

    def test_Data_insert_dimension(self):
        """Test Data.insert_dimension."""
        d = cfdm.Data([list(range(12))])
        self.assertEqual(d.shape, (1, 12))
        e = d.squeeze()
        self.assertEqual(e.shape, (12,))
        self.assertIsNone(d.squeeze(inplace=True))
        self.assertEqual(d.shape, (12,))

        d = cfdm.Data([list(range(12))])
        d.transpose(inplace=True)
        self.assertEqual(d.shape, (12, 1))
        e = d.squeeze()
        self.assertEqual(e.shape, (12,))
        self.assertIsNone(d.squeeze(inplace=True))
        self.assertEqual(d.shape, (12,))

        d.insert_dimension(0, inplace=True)
        d.insert_dimension(-1, inplace=True)
        self.assertEqual(d.shape, (1, 12, 1))
        e = d.squeeze()
        self.assertEqual(e.shape, (12,))
        e = d.squeeze(-1)
        self.assertEqual(e.shape, (1, 12))
        self.assertIsNone(e.squeeze(0, inplace=True))
        self.assertEqual(e.shape, (12,))

        d = e
        d.insert_dimension(0, inplace=True)
        d.insert_dimension(-1, inplace=True)
        d.insert_dimension(-1, inplace=True)
        self.assertEqual(d.shape, (1, 12, 1, 1))
        e = d.squeeze([0, 2])
        self.assertEqual(e.shape, (12, 1))

        array = np.arange(12).reshape(1, 4, 3)
        d = cfdm.Data(array)
        e = d.squeeze()
        f = e.insert_dimension(0)
        a = f.array
        self.assertTrue(np.allclose(a, array))

        with self.assertRaises(ValueError):
            d.insert_dimension(1000)

        # Dataset chunks
        d.nc_set_dataset_chunksizes((1, 4, 3))
        d.insert_dimension(0, inplace=True)
        self.assertEqual(d.nc_dataset_chunksizes(), (1, 1, 4, 3))
        d.insert_dimension(-1, inplace=True)
        self.assertEqual(d.nc_dataset_chunksizes(), (1, 1, 4, 3, 1))

        array = np.arange(12).reshape(3, 4)
        d = cfdm.Data(array)
        for i in (0, 1, 2, -3, -2, -1):
            self.assertEqual(
                d.insert_dimension(i).shape, np.expand_dims(array, i).shape
            )

    def test_Data_get_compressed_dimension(self):
        """Test Data.get_compressed_dimension."""
        d = cfdm.Data([[281, 279, 278, 279]])
        self.assertIsNone(d.get_compressed_dimension(None))

    def test_Data__format__(self):
        """Test Data.__format__"""
        d = cfdm.Data(9, "metres")
        self.assertEqual(f"{d}", "9 metres")
        self.assertEqual(f"{d!s}", "9 metres")
        self.assertEqual(f"{d!r}", "<Data(): 9 metres>")
        self.assertEqual(f"{d:.3f}", "9.000")

        d = cfdm.Data([[9]], "metres")
        self.assertEqual(f"{d}", "[[9]] metres")
        self.assertEqual(f"{d!s}", "[[9]] metres")
        self.assertEqual(f"{d!r}", "<Data(1, 1): [[9]] metres>")
        self.assertEqual(f"{d:.3f}", "9.000")

        d = cfdm.Data([9, 10], "metres")
        self.assertEqual(f"{d}", "[9, 10] metres")
        self.assertEqual(f"{d!s}", "[9, 10] metres")
        self.assertEqual(f"{d!r}", "<Data(2): [9, 10] metres>")
        with self.assertRaises(ValueError):
            f"{d:.3f}"

    def test_Data_orginal_filenames(self):
        """Test Data.original_filenames."""
        d = cfdm.Data(9, "metres")
        self.assertEqual(d.get_original_filenames(), set())

        self.assertIsNone(d._original_filenames(define="file1.nc"))
        self.assertEqual(
            d.get_original_filenames(), set([cfdm.abspath("file1.nc")])
        )

        self.assertIsNone(d._original_filenames(update=["file1.nc"]))
        self.assertEqual(len(d.get_original_filenames()), 1)

        d._original_filenames(update="file2.nc")
        self.assertEqual(len(d.get_original_filenames()), 2)

        d._original_filenames(update=["file1.nc", "file2.nc"])
        self.assertEqual(len(d.get_original_filenames()), 2)

        d._original_filenames(define="file3.nc")
        self.assertEqual(len(d.get_original_filenames()), 1)

        self.assertEqual(len(d._original_filenames(clear=True)), 1)
        self.assertEqual(d.get_original_filenames(), set())

        d._original_filenames(update=["file1.nc", "file2.nc"])
        self.assertEqual(len(d.get_original_filenames()), 2)

        # Check source
        e = cfdm.Data(source=d)
        self.assertEqual(
            e.get_original_filenames(), d.get_original_filenames()
        )

        # Check illegal parameter combinations
        with self.assertRaises(ValueError):
            d._original_filenames(define="file1.nc", update="file2.nc")

        with self.assertRaises(ValueError):
            d._original_filenames(define="file3.nc", clear=True)

        with self.assertRaises(ValueError):
            d._original_filenames(update="file4.nc", clear=True)

    def test_Data_first_element(self):
        """Test Data.first_element."""
        d = cfdm.Data(np.arange(6).reshape(1, 6, 1))
        self.assertEqual(d.first_element(), 0)

    def test_Data_second_element(self):
        """Test Data.second_element."""
        d = cfdm.Data(np.arange(6).reshape(1, 6, 1))
        self.assertEqual(d.second_element(), 1)

    def test_Data_last_element(self):
        """Test Data.last_element."""
        d = cfdm.Data(np.arange(6).reshape(1, 6, 1))
        self.assertEqual(d.last_element(), 5)

    def test_Data_sparse_array(self):
        """Test Data based on sparse arrays."""
        from scipy.sparse import csr_array

        indptr = np.array([0, 2, 3, 6])
        indices = np.array([0, 2, 2, 0, 1, 2])
        data = np.array([1, 2, 3, 4, 5, 6])
        s = csr_array((data, indices, indptr), shape=(3, 3))

        d = cfdm.Data(s)
        self.assertFalse((d.sparse_array != s).toarray().any())
        self.assertTrue((d.array == s.toarray()).all())

        d = cfdm.Data(s, dtype=float)
        self.assertEqual(d.sparse_array.dtype, float)

        # Can't mask sparse array during __init__
        mask = [[0, 0, 1], [0, 0, 0], [0, 0, 0]]
        with self.assertRaises(ValueError):
            cfdm.Data(s, mask=mask)

    def test_Data_masked_values(self):
        """Test Data.masked_values."""
        array = np.array([[1, 1.1, 2, 1.1, 3]])
        d = cfdm.Data(array)
        e = d.masked_values(1.1)
        ea = e.array
        a = np.ma.masked_values(
            array, 1.1, rtol=float(cfdm.rtol()), atol=float(cfdm.atol())
        )
        self.assertTrue(np.isclose(ea, a).all())
        self.assertTrue((ea.mask == a.mask).all())
        self.assertIsNone(d.masked_values(1.1, inplace=True))
        self.assertTrue(d.equals(e))

        array = np.array([[1, 1.1, 2, 1.1, 3]])
        d = cfdm.Data(array, mask_value=1.1)
        da = e.array
        self.assertTrue(np.isclose(da, a).all())
        self.assertTrue((da.mask == a.mask).all())

    def test_Data__int__(self):
        """Test Data.__int__"""
        for x in (-1.9, -1.5, -1.4, -1, 0, 1, 1.0, 1.4, 1.9):
            self.assertEqual(int(cfdm.Data(x)), int(x))
            self.assertEqual(int(cfdm.Data(x)), int(x))

        with self.assertRaises(Exception):
            _ = int(cfdm.Data([1, 2]))

    def test_Data_pad_missing(self):
        """Test Data.pad_missing."""
        d = cfdm.Data(np.arange(6).reshape(2, 3))

        g = d.pad_missing(1, to_size=5)
        self.assertEqual(g.shape, (2, 5))
        self.assertTrue(g[:, 3:].mask.array.all())

        self.assertIsNone(d.pad_missing(1, pad_width=(1, 2), inplace=True))
        self.assertEqual(d.shape, (2, 6))
        self.assertTrue(d[:, 0].mask.array.all())
        self.assertTrue(d[:, 4:].mask.array.all())

        e = d.pad_missing(0, pad_width=(0, 1))
        self.assertEqual(e.shape, (3, 6))
        self.assertTrue(e[2, :].mask.array.all())

        # Can't set both pad_width and to_size
        with self.assertRaises(ValueError):
            d.pad_missing(0, pad_width=(0, 1), to_size=99)

        # Axis out of bounds
        with self.assertRaises(ValueError):
            d.pad_missing(99, to_size=99)

    def test_Data_todict(self):
        """Test Data.todict."""
        d = cfdm.Data([1, 2, 3, 4], chunks=2)
        key = d.to_dask_array(_force_mask_hardness=False).name

        x = d.todict()
        self.assertIsInstance(x, dict)
        self.assertIn((key, 0), x)
        self.assertIn((key, 1), x)

        e = d[0]
        x = e.todict(graph="cull")
        self.assertIn((key, 0), x)
        self.assertNotIn((key, 1), x)

        e = d[0]
        x = e.todict(graph=None)
        self.assertIsInstance(x, dict)
        self.assertIn((key, 0), x)
        self.assertIn((key, 1), x)

        # Deprecated kwargs
        with self.assertRaises(DeprecationError):
            d.todict(optimize_graph=True)

    def test_Data_to_dask_array(self):
        """Test Data.to_dask_array."""
        d = cfdm.Data([1, 2, 3, 4], "m")
        dx = d.to_dask_array()
        self.assertIsInstance(dx, da.Array)
        self.assertTrue((d.array == dx.compute()).all())

    def test_Data_persist(self):
        """Test Data.persist."""
        d = cfdm.Data(9, "km")
        self.assertIsNone(d.persist(inplace=True))

        d = cfdm.Data([[1, 2, 3.0, 4]], "km", chunks=2)
        self.assertEqual(len(d.to_dask_array().dask.layers), 2)
        d.transpose(inplace=True)
        self.assertEqual(len(d.to_dask_array().dask.layers), 3)

        e = d.persist()
        self.assertIsInstance(e, cfdm.Data)
        self.assertEqual(len(e.to_dask_array().dask.layers), 2)
        self.assertEqual(d.npartitions, 2)
        self.assertEqual(e.npartitions, d.npartitions)
        self.assertTrue(e.equals(d))

    def test_Data_cull_graph(self):
        """Test Data.cull_graph."""
        d = cfdm.Data([1, 2, 3, 4, 5], chunks=3)
        d = d[:2]
        nkeys = len(dict(d.to_dask_array().dask))

        # Check that there are fewer keys after culling
        e = d.cull_graph(inplace=False)
        self.assertIsInstance(e, cfdm.Data)
        self.assertLess(len(dict(e.to_dask_array().dask)), nkeys)

        # Check in-place (the default)
        self.assertIsNone(d.cull_graph())
        self.assertLess(len(dict(d.to_dask_array().dask)), nkeys)

    def test_Data_npartitions(self):
        """Test Data.npartitions."""
        d = cfdm.Data.empty((4, 5), chunks=(2, 4))
        self.assertEqual(d.npartitions, 4)

    def test_Data_numblocks(self):
        """Test Data.numblocks."""
        d = cfdm.Data.empty((4, 5), chunks=(2, 4))
        self.assertEqual(d.numblocks, (2, 2))

    def test_Data_clear_after_dask_update(self):
        """Test Data._clear_after_dask_update."""
        d = cfdm.Data([1, 2, 3], "m")
        dx = d.to_dask_array()

        d.first_element()
        d.second_element()
        d.last_element()

        self.assertTrue(d._get_cached_elements())

        _ALL = cfdm.Data._ALL
        _CACHE = cfdm.Data._CACHE

        d._set_dask(dx, clear=_ALL ^ _CACHE)
        self.assertTrue(d._get_cached_elements())

        d._set_dask(dx, clear=_ALL)
        self.assertFalse(d._get_cached_elements())

    def test_Data_months_years(self):
        """Test Data with 'months/years since' units specifications."""
        calendar = "360_day"
        d = cfdm.Data(
            [1.0, 2],
            units=cfdm.Units("months since 2000-1-1", calendar=calendar),
        )
        self.assertTrue((d.array == np.array([1.0, 2])).all())
        a = np.array(
            [
                cftime.Datetime360Day(2000, 2, 1, 10, 29, 3, 831223),
                cftime.Datetime360Day(2000, 3, 1, 20, 58, 7, 662446),
            ]
        )

        self.assertTrue((d.datetime_array == a).all())

        calendar = "standard"
        d = cfdm.Data(
            [1.0, 2],
            units=cfdm.Units("months since 2000-1-1", calendar=calendar),
        )
        self.assertTrue((d.array == np.array([1.0, 2])).all())
        a = np.array(
            [
                cftime.DatetimeGregorian(2000, 1, 31, 10, 29, 3, 831223),
                cftime.DatetimeGregorian(2000, 3, 1, 20, 58, 7, 662446),
            ]
        )
        self.assertTrue((d.datetime_array == a).all())

        calendar = "360_day"
        d = cfdm.Data(
            [1.0, 2],
            units=cfdm.Units("years since 2000-1-1", calendar=calendar),
        )
        self.assertTrue((d.array == np.array([1.0, 2])).all())
        a = np.array(
            [
                cftime.Datetime360Day(2001, 1, 6, 5, 48, 45, 974678),
                cftime.Datetime360Day(2002, 1, 11, 11, 37, 31, 949357),
            ]
        )
        self.assertTrue((d.datetime_array == a).all())

        calendar = "standard"
        d = cfdm.Data(
            [1.0, 2],
            units=cfdm.Units("years since 2000-1-1", calendar=calendar),
        )
        self.assertTrue((d.array == np.array([1.0, 2])).all())
        a = np.array(
            [
                cftime.DatetimeGregorian(2000, 12, 31, 5, 48, 45, 974678),
                cftime.DatetimeGregorian(2001, 12, 31, 11, 37, 31, 949357),
            ]
        )
        self.assertTrue((d.datetime_array == a).all())

    def test_Data_datetime_array(self):
        """Test Data.datetime_array."""
        d = cfdm.Data([11292.5, 11293], units="days since 1970-1-1")
        dt = d.datetime_array
        self.assertEqual(dt[0], datetime.datetime(2000, 12, 1, 12, 0))
        self.assertEqual(dt[1], datetime.datetime(2000, 12, 2, 0, 0))

        d[0] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[0], np.ma.masked)
        self.assertEqual(dt[1], datetime.datetime(2000, 12, 2, 0, 0))

        d = cfdm.Data(11292.5, units="days since 1970-1-1")
        dt = d.datetime_array
        self.assertEqual(dt[()], datetime.datetime(2000, 12, 1, 12, 0))

        d[()] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[()], np.ma.masked)

        # Scalar array
        for d, x in zip(
            [
                cfdm.Data(11292.5, "days since 1970-1-1"),
                cfdm.Data("2000-12-1 12:00", dt=True),
            ],
            [11292.5, 0],
        ):
            a = d.datetime_array
            self.assertEqual(a.shape, ())
            self.assertEqual(
                a, np.array(cftime.DatetimeGregorian(2000, 12, 1, 12, 0))
            )

            a = d.array
            self.assertEqual(a.shape, ())
            self.assertEqual(a, x)

        # Non-scalar array
        for d, x in zip(
            [
                cfdm.Data([[11292.5, 11293.5]], "days since 1970-1-1"),
                cfdm.Data([["2000-12-1 12:00", "2000-12-2 12:00"]], dt=True),
            ],
            ([[11292.5, 11293.5]], [[0, 1]]),
        ):
            a = d.datetime_array
            self.assertTrue(
                (
                    a
                    == np.array(
                        [
                            [
                                cftime.DatetimeGregorian(2000, 12, 1, 12, 0),
                                cftime.DatetimeGregorian(2000, 12, 2, 12, 0),
                            ]
                        ]
                    )
                ).all()
            )

            a = d.array
            self.assertTrue((a == x).all())

    def test_Data_datetime_as_string(self):
        """Test the `datetime_as_string` Data property."""
        d = cfdm.Data([11292.5, 11293.5], "days since 1970-1-1")
        array = d.datetime_as_string
        self.assertEqual(array.dtype.kind, "U")

        self.assertTrue(
            (array == ["2000-12-01 12:00:00", "2000-12-02 12:00:00"]).all()
        )

    def test_Data_compute(self):
        """Test Data.compute."""
        # Scalar numeric array
        d = cfdm.Data(9, "km")
        a = d.compute()
        self.assertIsInstance(a, np.ndarray)
        self.assertEqual(a.shape, ())
        self.assertEqual(a, np.array(9))
        d[...] = cfdm.masked
        a = d.compute()
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], np.ma.masked)

        # Non-scalar numeric array
        b = np.arange(24).reshape(2, 1, 3, 4)
        d = cfdm.Data(b, "km", fill_value=-123)
        a = d.compute()
        self.assertTrue((a == b).all())

        # Fill value
        d[0, 0, 0, 0] = cfdm.masked
        self.assertEqual(d.compute().fill_value, d.get_fill_value())

        # Date-time array
        d = cfdm.Data([["2000-12-3 12:00"]], "days since 2000-12-01", dt=True)
        self.assertEqual(d.compute(), 2.5)

    def test_Data_chunks(self):
        """Test Data.chunks."""
        dx = da.empty((4, 5), chunks=(2, 4))
        d = cfdm.Data.empty((4, 5), chunks=(2, 4))
        self.assertEqual(d.chunks, dx.chunks)

    def test_Data_rechunk(self):
        """Test Data.rechunk."""
        dx = da.empty((4, 5), chunks=(2, 4)).rechunk(-1)
        d = cfdm.Data.empty((4, 5), chunks=(2, 4)).rechunk(-1)
        self.assertEqual(d.chunks, dx.chunks)

        d = cfdm.Data.empty((4, 5), chunks=(2, 4))
        e = d.copy()
        self.assertIsNone(e.rechunk(-1, inplace=True))
        self.assertEqual(e.chunks, ((4,), (5,)))
        self.assertTrue(e.equals(d))

        # Test rechunking after a __getitem__
        e = d[:2].rechunk((2, 5))
        self.assertTrue(e.equals(d[:2]))

        d = cfdm.Data.empty((4, 5), chunks=(4, 5))
        e = d[:2].rechunk((1, 3))
        self.assertTrue(e.equals(d[:2]))

    def test_Data_reshape(self):
        """Test Data.reshape."""
        a = np.arange(12).reshape(3, 4)
        d = cfdm.Data(a)
        self.assertIsNone(d.reshape(*d.shape, inplace=True))
        self.assertEqual(d.shape, a.shape)

        for original_shape, new_shape, chunks in (
            ((10,), (10,), (3, 3, 4)),
            ((10,), (10, 1, 1), 5),
            ((10,), (1, 10), 5),
            ((24,), (2, 3, 4), 12),
            ((1, 24), (2, 3, 4), 12),
            ((2, 3, 4), (24,), (1, 3, 4)),
            ((2, 3, 4), (24,), 4),
            ((2, 3, 4), (24, 1), 4),
            ((2, 3, 4), (1, 24), 4),
            ((4, 4, 1), (4, 4), 2),
            ((4, 4), (4, 4, 1), 2),
            ((1, 4, 4), (4, 4), 2),
            ((1, 4, 4), (4, 4, 1), 2),
            ((1, 4, 4), (1, 1, 4, 4), 2),
            ((4, 4), (1, 4, 4, 1), 2),
            ((4, 4), (1, 4, 4), 2),
            ((2, 3), (2, 3), (1, 2)),
            ((2, 3), (3, 2), 3),
            ((4, 2, 3), (4, 6), 4),
            ((3, 4, 5, 6), (3, 4, 5, 6), (2, 3, 4, 5)),
            ((), (1,), 1),
            ((1,), (), 1),
            ((24,), (3, 8), 24),
            ((24,), (4, 6), 6),
            ((24,), (4, 3, 2), 6),
            ((24,), (4, 6, 1), 6),
            ((24,), (4, 6), (6, 12, 6)),
            ((64, 4), (8, 8, 4), (16, 2)),
            ((4, 64), (4, 8, 4, 2), (2, 16)),
            ((4, 8, 4, 2), (2, 1, 2, 32, 2), (2, 4, 2, 2)),
            ((4, 1, 4), (4, 4), (2, 1, 2)),
            ((0, 10), (0, 5, 2), (5, 5)),
            ((5, 0, 2), (0, 10), (5, 2, 2)),
            ((0,), (2, 0, 2), (4,)),
            ((2, 0, 2), (0,), (4, 4, 4)),
            ((2, 3, 4), -1, -1),
        ):
            a = np.random.randint(10, size=original_shape)
            d = cfdm.Data(a, chunks=chunks)

            a = a.reshape(new_shape)
            d = d.reshape(new_shape)

            self.assertEqual(d.shape, a.shape)
            self.assertTrue((d.array == a).all())

        # Test setting of _axes
        d = cfdm.Data(8)
        self.assertEqual(len(d.reshape(1, 1)._axes), 2)

        d = cfdm.Data([8, 9])
        self.assertEqual(len(d.reshape(1, 2)._axes), 2)

        # Test when underlying data is in a `FileAarray` object
        # (i.e. on disk)
        f = cfdm.write(self.f0, file_A)
        f = cfdm.read(file_A)[0]
        d = f.data
        e = d.reshape((1,) + d.shape)
        self.assertTrue(np.allclose(e[0], d))

    def test_Data_get_units(self):
        """Test Data.get_units."""
        for units in ("", "m", "days since 2000-01-01"):
            d = cfdm.Data(1, units)
            self.assertEqual(d.get_units(), units)

        d = cfdm.Data(1)
        with self.assertRaises(ValueError):
            d.get_units()

    def test_Data_set_calendar(self):
        """Test Data.set_calendar."""
        d = cfdm.Data(1, "days since 2000-01-01")
        d.set_calendar("standard")
        d.set_calendar("noleap")

        d = cfdm.Data(1, "m")
        d.set_calendar("noleap")
        self.assertEqual(d.Units, cfdm.Units("m"))

    def test_Data_set_units(self):
        """Test Data.set_units."""
        for units in (None, "", "m", "days since 2000-01-01"):
            d = cfdm.Data(1, units)
            self.assertEqual(d.Units, cfdm.Units(units))

        d = cfdm.Data(1, "m")
        d.set_units("km")
        self.assertEqual(d.Units, cfdm.Units("km"))

        d = cfdm.Data(1, "days since 2000-01-01", calendar="noleap")
        d.set_units("days since 1999-12-31")
        self.assertEqual(
            d.Units, cfdm.Units("days since 1999-12-31", calendar="noleap")
        )
        d.set_units("km")
        self.assertEqual(d.Units, cfdm.Units("km"))

    def test_Data_tolist(self):
        """Test Data.tolist."""
        for x in (1, [1, 2], [[1, 2], [3, 4]]):
            d = cfdm.Data(x)
            e = d.tolist()
            self.assertEqual(e, np.array(x).tolist())
            self.assertTrue(d.equals(cfdm.Data(e)))

    def test_Data_data(self):
        """Test Data.data."""
        for d in [
            cfdm.Data(1),
            cfdm.Data([1, 2], fill_value=0),
            cfdm.Data([1, 2], "m"),
            cfdm.Data([1, 2], mask=[1, 0], units="m"),
            cfdm.Data([[0, 1, 2], [3, 4, 5]], chunks=2),
        ]:
            self.assertIs(d.data, d)

    def test_Data_hardmask(self):
        """Test Data.hardmask."""
        d = cfdm.Data([1, 2, 3])
        d.hardmask = True
        self.assertTrue(d.hardmask)
        d[0] = cfdm.masked
        self.assertTrue((d.array.mask == [True, False, False]).all())
        d[...] = 999
        self.assertTrue((d.array.mask == [True, False, False]).all())
        d.hardmask = False
        self.assertFalse(d.hardmask)
        d[...] = -1
        self.assertTrue((d.array.mask == [False, False, False]).all())

    def test_Data_soften_mask(self):
        """Test Data.soften_mask."""
        d = cfdm.Data([1, 2, 3], hardmask=True)
        d.soften_mask()
        self.assertFalse(d.hardmask)
        d[0] = cfdm.masked
        self.assertEqual(d[0].array, np.ma.masked)
        d[0] = 99
        self.assertEqual(d[0].array, 99)

    def test_Data_get_data(self):
        """Test Data.get_data."""
        d = cfdm.Data(9)
        self.assertIs(d, d.get_data())

    def test_Data__init__datetime(self):
        """Test Data.__init__ for datetime objects."""
        dt = cftime.DatetimeGregorian(2000, 1, 1)
        for a in (dt, [dt], [[dt]]):
            d = cfdm.Data(a)
            self.assertEqual(d.array, 0)

        dt = [dt, cftime.DatetimeGregorian(2000, 2, 1)]
        d = cfdm.Data(dt)
        self.assertTrue((d.array == [0, 31]).all())

        dt = np.ma.array(dt, mask=[True, False])
        d = cfdm.Data(dt)
        self.assertTrue((d.array == [-999, 0]).all())

        units = cfdm.Units("days since 2000-01-01", calendar="noleap")
        for array, dt in zip(
            (
                [1, 2],
                ["2000-01-02", "2000-01-03"],
                [
                    cftime.DatetimeNoLeap(2000, 1, 2),
                    cftime.DatetimeNoLeap(2000, 1, 3),
                ],
            ),
            (False, True, False),
        ):
            d = cfdm.Data(array, units=units, dt=dt)
            self.assertTrue((d.array == [1, 2]).all())
            self.assertTrue(
                (
                    d.datetime_array
                    == [
                        cftime.DatetimeNoLeap(2000, 1, 2),
                        cftime.DatetimeNoLeap(2000, 1, 3),
                    ]
                ).all()
            )

    def test_Data_mask(self):
        """Test Data.mask."""
        # Test for a masked Data object (having some masked points)
        a = np.ma.arange(12).reshape(3, 4)
        a[1, 1] = np.ma.masked
        d = cfdm.Data(a, units="m", chunks=(2, 2))
        self.assertTrue((a == d.array).all())
        self.assertTrue((a.mask == d.mask.array).all())
        self.assertEqual(d.mask.shape, d.shape)
        self.assertEqual(d.mask.dtype, bool)
        self.assertEqual(d.mask.Units, cfdm.Units(None))
        self.assertTrue(d.mask.hardmask)
        self.assertIn(True, d.mask.array)

        # Test for a non-masked Data object
        a2 = np.arange(-100, 200.0, dtype=float).reshape(3, 4, 5, 5)
        d2 = cfdm.Data(a2, units="m", chunks=(1, 2, 3, 4))
        d2[...] = a2
        self.assertTrue((a2 == d2.array).all())
        self.assertEqual(d2.shape, d2.mask.shape)
        self.assertEqual(d2.mask.dtype, bool)
        self.assertEqual(d2.mask.Units, cfdm.Units(None))
        self.assertTrue(d2.mask.hardmask)
        self.assertNotIn(True, d2.mask.array)

        # Test for a masked Data object of string type, including chunking
        a3 = np.ma.array(["one", "two", "four"], dtype="S4")
        a3[1] = np.ma.masked
        d3 = cfdm.Data(a3, "m", chunks=(3,))
        self.assertTrue((a3 == d3.array).all())
        self.assertEqual(d3.shape, d3.mask.shape)
        self.assertEqual(d3.mask.dtype, bool)
        self.assertEqual(d3.mask.Units, cfdm.Units(None))
        self.assertTrue(d3.mask.hardmask)
        self.assertTrue(d3.mask.array[1], True)

    def test_Data__init__dtype_mask(self):
        """Test Data.__init__ with `dtype` and `mask` keywords."""
        for m in (1, 20, True):
            d = cfdm.Data([[1, 2, 3], [4, 5, 6]], mask=m)
            self.assertFalse(np.ma.count(d.array))
            self.assertEqual(d.shape, (2, 3))

        for m in (0, False):
            d = cfdm.Data([[1, 2, 3], [4, 5, 6]], mask=m)
            self.assertEqual(np.ma.count(d.array), d.size)
            self.assertEqual(d.shape, (2, 3))

        d = cfdm.Data([[1, 2, 3], [4, 5, 6]], mask=[[0], [1]])
        self.assertEqual(np.ma.count(d.array), 3)
        self.assertEqual(d.shape, (2, 3))

        d = cfdm.Data([[1, 2, 3], [4, 5, 6]], mask=[0, 1, 1])
        self.assertEqual(np.ma.count(d.array), 2)
        self.assertEqual(d.shape, (2, 3))

        d = cfdm.Data([[1, 2, 3], [4, 5, 6]], mask=[[0, 1, 0], [1, 0, 1]])
        self.assertEqual(np.ma.count(d.array), 3)
        self.assertEqual(d.shape, (2, 3))

        a = np.ma.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        d = cfdm.Data([[280, -99, -99, -99], [281, 279, 278, 279]])
        self.assertEqual(d.dtype, np.dtype(int))

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertEqual(d.mask.shape, a.mask.shape)
        self.assertTrue((d.array == a).all())
        self.assertTrue((d.mask.array == np.ma.getmaskarray(a)).all())

        a = np.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]], dtype=float
        )
        mask = np.ma.masked_all(a.shape).mask

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]], dtype=float
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertEqual(d.mask.shape, mask.shape)
        self.assertTrue((d.array == a).all())
        self.assertTrue((d.mask.array == np.ma.getmaskarray(a)).all())

        # Mask broadcasting
        a = np.ma.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]],
            dtype=float,
            mask=[[0, 1, 1, 0], [0, 1, 1, 0]],
        )

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]],
            dtype=float,
            mask=[0, 1, 1, 0],
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertEqual(d.mask.shape, a.mask.shape)
        self.assertTrue((d.array == a).all())
        self.assertTrue((d.mask.array == np.ma.getmaskarray(a)).all())

    def test_Data__getitem__(self):
        """Test Data.__getitem__"""
        d = cfdm.Data(np.ma.arange(450).reshape(9, 10, 5), chunks=(4, 5, 1))

        for indices in (
            Ellipsis,
            (slice(None), slice(None)),
            (slice(None), Ellipsis),
            (Ellipsis, slice(None)),
            (Ellipsis, slice(None), Ellipsis),
        ):
            self.assertEqual(d[indices].shape, d.shape)

        for indices in (
            ([1, 3, 4], slice(None), [2, -1]),
            (slice(0, 6, 2), slice(None), [2, -1]),
            (slice(0, 6, 2), slice(None), slice(2, 5, 2)),
            (slice(0, 6, 2), list(range(10)), slice(2, 5, 2)),
        ):
            self.assertEqual(d[indices].shape, (3, 10, 2))

        for indices in (
            (slice(0, 6, 2), -2, [2, -1]),
            (slice(0, 6, 2), -2, slice(2, 5, 2)),
        ):
            self.assertEqual(d[indices].shape, (3, 1, 2))

        for indices in (
            ([1, 3, 4], -2, [2, -1]),
            ([4, 3, 1], -2, [2, -1]),
            ([1, 4, 3], -2, [2, -1]),
            ([4, 1, 4], -2, [2, -1]),
        ):
            e = d[indices]
            self.assertEqual(e.shape, (3, 1, 2))
            self.assertEqual(e._axes, d._axes)

        d.__keepdims_indexing__ = False
        self.assertFalse(d.__keepdims_indexing__)
        for indices in (
            ([1, 3, 4], -2, [2, -1]),
            (slice(0, 6, 2), -2, [2, -1]),
            (slice(0, 6, 2), -2, slice(2, 5, 2)),
            ([1, 4, 3], -2, [2, -1]),
            ([4, 3, 4], -2, [2, -1]),
            ([1, 4, 4], -2, [2, -1]),
        ):
            e = d[indices]
            self.assertFalse(e.__keepdims_indexing__)
            self.assertEqual(e.shape, (3, 2))
            self.assertEqual(e._axes, d._axes[0::2])

        self.assertFalse(d.__keepdims_indexing__)
        d.__keepdims_indexing__ = True
        self.assertTrue(d.__keepdims_indexing__)

        d = cfdm.Data(np.ma.arange(24).reshape(3, 8))
        e = d[0, 2:4]

        # Keepdims indexing
        d = cfdm.Data([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(d[0].shape, (1, 3))
        self.assertEqual(d[:, 1].shape, (2, 1))
        self.assertEqual(d[0, 1].shape, (1, 1))
        d.__keepdims_indexing__ = False
        self.assertEqual(d[0].shape, (3,))
        self.assertEqual(d[:, 1].shape, (2,))
        self.assertEqual(d[0, 1].shape, ())
        d.__keepdims_indexing__ = True

        # Orthogonal indexing
        self.assertEqual(d[[0], [0, 2]].shape, (1, 2))
        self.assertEqual(d[[0, 1], [0, 2]].shape, (2, 2))
        self.assertEqual(d[[0, 1], [2]].shape, (2, 1))

        # Indices that have a 'to_dask_array' method
        d = cfdm.Data(np.arange(45).reshape(9, 5), chunks=(4, 5))
        indices = (cfdm.Data([1, 3]), cfdm.Data([0, 1, 2, 3, 4]) > 1)
        self.assertEqual(d[indices].shape, (2, 3))

        # ... and with a masked array
        a = d.array
        d = cfdm.Data(np.ma.where(a < 20, np.ma.masked, a))
        e = d[cfdm.Data([0, 7]), 0]
        f = cfdm.Data([-999, 35], mask=[True, False]).reshape(2, 1)
        self.assertTrue(e.equals(f))

        # Chained subspaces reading from disk
        f = cfdm.read(self.filename, netcdf_backend="h5netcdf")[0]
        d = f.data

        a = d[:1, [1, 3, 4], :][:, [True, False, True], ::-2].array
        b = d.array[:1, [1, 3, 4], :][:, [True, False, True], ::-2]
        self.assertTrue((a == b).all())

        d.__keepdims_indexing__ = False
        a = d[0, [1, 3, 4], :][[True, False, True], ::-2].array
        b = d.array[0, [1, 3, 4], :][[True, False, True], ::-2]
        self.assertTrue((a == b).all())

        # Dataset chunks
        d = cfdm.Data(np.arange(12).reshape(1, 4, 3))
        d.nc_set_dataset_chunksizes((1, 4, 3))
        e = d[0, :2, :]
        self.assertEqual(e.nc_dataset_chunksizes(), (1, 2, 3))

        # Integer-list indices that trigger dask optimisation (e.g. a
        # non-monotonic integer list that spans multiple chunks, and
        # applies to underlying cfdm Array objects).
        cfdm.write(self.f0, file_A)
        d = cfdm.read(file_A, dask_chunks=3)[0].data
        self.assertTrue(
            (d[0, [4, 0, 3, 1]].array == [[0.018, 0.007, 0.014, 0.034]]).all()
        )

    def test_Data_BINARY_AND_UNARY_OPERATORS(self):
        """Test arithmetic, logical and comparison operators on Data."""
        a = np.arange(3 * 4 * 5).reshape(3, 4, 5)
        b = a[...]
        b[2:] = a[2:] + 1

        d = cfdm.Data(a)
        e = cfdm.Data(b)

        self.assertTrue((d == e).equals(cfdm.Data(a == b)))
        self.assertTrue((d != e).equals(cfdm.Data(a != b)))
        self.assertTrue((d >= e).equals(cfdm.Data(a >= b)))
        self.assertTrue((d <= e).equals(cfdm.Data(a <= b)))
        self.assertTrue((d > e).equals(cfdm.Data(a > b)))
        self.assertTrue((d < e).equals(cfdm.Data(a < b)))

        self.assertTrue((d & e).equals(cfdm.Data(a & b)))
        self.assertTrue((d | e).equals(cfdm.Data(a | b)))
        self.assertTrue((d ^ e).equals(cfdm.Data(a ^ b)))
        self.assertTrue((d << e).equals(cfdm.Data(a << b)))
        self.assertTrue((d >> e).equals(cfdm.Data(a >> b)))

        self.assertTrue(d.__rand__(e).equals(cfdm.Data(a.__rand__(b))))
        self.assertTrue(d.__ror__(e).equals(cfdm.Data(a.__ror__(b))))
        self.assertTrue(d.__rxor__(e).equals(cfdm.Data(a.__rxor__(b))))
        self.assertTrue(d.__rshift__(e).equals(cfdm.Data(a.__rshift__(b))))
        self.assertTrue(d.__rlshift__(e).equals(cfdm.Data(a.__rlshift__(b))))
        self.assertTrue(d.__rrshift__(e).equals(cfdm.Data(a.__rrshift__(b))))

        a &= b
        d &= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a |= b
        d |= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a ^= b
        d ^= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a <<= b
        d <<= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a >>= b
        d >>= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a &= b
        d &= e
        self.assertTrue(d.equals(cfdm.Data(a)))
        a &= b
        d &= e
        self.assertTrue(d.equals(cfdm.Data(a)))

        self.assertTrue((~d).equals(cfdm.Data(~a)))
        self.assertTrue((-d).equals(cfdm.Data(-a)))
        self.assertTrue((+d).equals(cfdm.Data(+a)))
        self.assertTrue((abs(d)).equals(cfdm.Data(abs(a))))

    def test_Data__len__(self):
        """Test Data.__len__"""
        self.assertEqual(3, len(cfdm.Data([1, 2, 3])))
        self.assertEqual(2, len(cfdm.Data([[1, 2, 3], [4, 5, 6]])))
        self.assertEqual(1, len(cfdm.Data([[1, 2, 3]])))

        # len() of unsized object
        with self.assertRaises(TypeError):
            len(cfdm.Data(1))

    def test_Data__float__(self):
        """Test Data.__float__"""
        for x in (-1.9, -1.5, -1.4, -1, 0, 1, 1.0, 1.4, 1.9):
            self.assertEqual(float(cfdm.Data(x)), float(x))
            self.assertEqual(float(cfdm.Data(x)), float(x))

        with self.assertRaises(TypeError):
            float(cfdm.Data([1, 2]))

    def test_Data_del_units(self):
        """Test Data.del_units."""
        d = cfdm.Data(1)
        with self.assertRaises(ValueError):
            d.del_units()

        d = cfdm.Data(1, "m")
        self.assertEqual(d.del_units(), "m")
        with self.assertRaises(ValueError):
            d.del_units()

        d = cfdm.Data(1, "days since 2000-1-1")
        self.assertEqual(d.del_units(), "days since 2000-1-1")
        with self.assertRaises(ValueError):
            d.del_units()

        d = cfdm.Data(1, "days since 2000-1-1", calendar="noleap")
        self.assertEqual(d.del_units(), "days since 2000-1-1")
        self.assertEqual(d.Units, cfdm.Units(None, "noleap"))
        with self.assertRaises(ValueError):
            d.del_units()

    def test_Data_del_calendar(self):
        """Test Data.del_calendar."""
        for units in (None, "", "m", "days since 2000-1-1"):
            d = cfdm.Data(1, units)
            with self.assertRaises(ValueError):
                d.del_calendar()

        d = cfdm.Data(1, "days since 2000-1-1", calendar="noleap")
        self.assertEqual(d.del_calendar(), "noleap")
        with self.assertRaises(ValueError):
            d.del_calendar()

    def test_Data_has_units(self):
        """Test Data.has_units."""
        d = cfdm.Data(1, "")
        self.assertTrue(d.has_units())
        d = cfdm.Data(1, "m")
        self.assertTrue(d.has_units())

        d = cfdm.Data(1)
        self.assertFalse(d.has_units())
        d = cfdm.Data(1, calendar="noleap")
        self.assertFalse(d.has_units())

    def test_Data_has_calendar(self):
        """Test Data.has_calendar."""
        d = cfdm.Data(1, "days since 2000-1-1", calendar="noleap")
        self.assertTrue(d.has_calendar())

        for units in (None, "", "m", "days since 2000-1-1"):
            d = cfdm.Data(1, units)
            self.assertFalse(d.has_calendar())

    def test_Data__init__compression(self):
        """Test Data initialised from compressed data sources."""
        # Ragged
        for f in cfdm.read("DSG_timeSeries_contiguous.nc"):
            f = f.data
            d = cfdm.Data(cfdm.RaggedContiguousArray(source=f.source()))
            self.assertTrue((d.array == f.array).all())

        for f in cfdm.read("DSG_timeSeries_indexed.nc"):
            f = f.data
            d = cfdm.Data(cfdm.RaggedIndexedArray(source=f.source()))
            self.assertTrue((d.array == f.array).all())

        for f in cfdm.read("DSG_timeSeriesProfile_indexed_contiguous.nc"):
            f = f.data
            d = cfdm.Data(cfdm.RaggedIndexedContiguousArray(source=f.source()))
            self.assertTrue((d.array == f.array).all())

        # Ragged bounds
        f = cfdm.read("DSG_timeSeriesProfile_indexed_contiguous.nc")[0]
        f = f.construct("long_name=height above mean sea level").bounds.data
        d = cfdm.Data(cfdm.RaggedIndexedContiguousArray(source=f.source()))
        self.assertTrue((d.array == f.array).all())

        # Gathered
        for f in cfdm.read("gathered.nc"):
            f = f.data
            d = cfdm.Data(cfdm.GatheredArray(source=f.source()))
            self.assertTrue((d.array == f.array).all())

        # Subsampled
        f = cfdm.read("subsampled_2.nc")[-3]
        f = f.construct("longitude").data
        d = cfdm.Data(cfdm.SubsampledArray(source=f.source()))
        self.assertTrue((d.array == f.array).all())

    def test_Data_empty(self):
        """Test Data.empty."""
        for shape, dtype_in, dtype_out in zip(
            [(), (3,), (4, 5)], [None, int, bool], [float, int, bool]
        ):
            d = cfdm.Data.empty(shape, dtype=dtype_in, chunks=-1)
            self.assertEqual(d.shape, shape)
            self.assertEqual(d.dtype, dtype_out)

    def test_Data__iter__(self):
        """Test Data.__iter__"""
        for d in (
            cfdm.Data([1, 2, 3], "metres"),
            cfdm.Data([[1, 2], [3, 4]], "metres"),
        ):
            d.__keepdims_indexing__ = False
            for i, e in enumerate(d):
                self.assertTrue(e.equals(d[i]))

        for d in (
            cfdm.Data([1, 2, 3], "metres"),
            cfdm.Data([[1, 2], [3, 4]], "metres"),
        ):
            d.__keepdims_indexing__ = True
            for i, e in enumerate(d):
                out = d[i]
                self.assertTrue(e.equals(out.reshape(out.shape[1:])))

        # iteration over a 0-d Data
        with self.assertRaises(TypeError):
            list(cfdm.Data(99, "metres"))

    def test_Data__bool__(self):
        """Test Data.__bool__"""
        for x in (1, 1.5, True, "x"):
            self.assertTrue(bool(cfdm.Data(x)))
            self.assertTrue(bool(cfdm.Data([[x]])))

        for x in (0, 0.0, False, ""):
            self.assertFalse(bool(cfdm.Data(x)))
            self.assertFalse(bool(cfdm.Data([[x]])))

        with self.assertRaises(ValueError):
            bool(cfdm.Data([]))

        with self.assertRaises(ValueError):
            bool(cfdm.Data([1, 2]))

    def test_Data_fill_value(self):
        """Test the `fill_value` Data property."""
        d = cfdm.Data([1, 2], "m")
        self.assertIsNone(d.fill_value)
        d.fill_value = 999
        self.assertEqual(d.fill_value, 999)
        del d.fill_value
        self.assertIsNone(d.fill_value)

    def test_Data_uncompress(self):
        """Test Data.uncompress."""
        f = cfdm.read("DSG_timeSeries_contiguous.nc")[0]
        a = f.data.array
        d = cfdm.Data(cfdm.RaggedContiguousArray(source=f.data.source()))

        self.assertTrue(d.get_compression_type())
        self.assertTrue((d.array == a).all())

        self.assertIsNone(d.uncompress(inplace=True))
        self.assertFalse(d.get_compression_type())
        self.assertTrue((d.array == a).all())

    def test_Data__atol(self):
        """Test Data._atol."""
        d = cfdm.Data(1)
        self.assertEqual(d._atol, cfdm.atol())
        with cfdm.atol(0.001):
            self.assertEqual(d._atol, 0.001)

    def test_Data__rtol(self):
        """Test Data._rtol."""
        d = cfdm.Data(1)
        self.assertEqual(d._rtol, cfdm.rtol())
        with cfdm.rtol(0.001):
            self.assertEqual(d._rtol, 0.001)

    def test_Data_compressed_array(self):
        """Test Data.compressed_array."""
        f = cfdm.read("DSG_timeSeries_contiguous.nc")[0]
        f = f.data
        d = cfdm.Data(cfdm.RaggedContiguousArray(source=f.source()))
        self.assertTrue((d.compressed_array == f.compressed_array).all())

        d = cfdm.Data([1, 2, 3], "m")
        with self.assertRaises(ValueError):
            d.compressed_array

    def test_Data_get_compressed(self):
        """Test the Data methods which get compression properties."""
        # Compressed
        f = cfdm.read("DSG_timeSeries_contiguous.nc")[0]
        f = f.data
        d = cfdm.Data(cfdm.RaggedContiguousArray(source=f.source()))

        self.assertEqual(d.get_compressed_axes(), f.get_compressed_axes())
        self.assertEqual(d.get_compression_type(), f.get_compression_type())
        self.assertEqual(
            d.get_compressed_dimension(), f.get_compressed_dimension()
        )

        # Uncompressed
        d = cfdm.Data(9)

        self.assertEqual(d.get_compressed_axes(), [])
        self.assertEqual(d.get_compression_type(), "")

        with self.assertRaises(ValueError):
            d.get_compressed_dimension()

    def test_Data_Units(self):
        """Test Data.Units."""
        d = cfdm.Data(100, "m")
        self.assertEqual(d.Units, cfdm.Units("m"))

        d.Units = cfdm.Units("km")
        self.assertEqual(d.Units, cfdm.Units("km"))

        # Assign units when none were set
        d = cfdm.Data(100)
        d.Units = cfdm.Units("km")
        self.assertEqual(d.Units, cfdm.Units("km"))

        d = cfdm.Data(100, "")

        # Delete units
        del d.Units
        self.assertEqual(d.Units, cfdm.Units(None))

    def test_Data_get_filenames(self):
        """Test Data.get_filenames."""
        d = cfdm.Data.empty((5, 8), float, chunks=4)
        self.assertEqual(d.get_filenames(), set())

        f = self.f0
        cfdm.write(f, file_A)

        d = cfdm.read(file_A, dask_chunks=4)[0].data
        self.assertEqual(d.get_filenames(), set([file_A]))
        d.persist(inplace=True)
        self.assertEqual(d.data.get_filenames(), set())

        # Per chunk
        d = cfdm.read(file_A, dask_chunks="128 B")[0].data
        self.assertEqual(d.numblocks, (2, 2))
        f = d.get_filenames(per_chunk=True)
        self.assertEqual(f.shape, d.numblocks)
        self.assertTrue((f == [[file_A, file_A], [file_A, file_A]]).all())

    def test_Data_chunk_indices(self):
        """Test Data.chunk_indices."""
        d = cfdm.Data(
            np.arange(405).reshape(3, 9, 15), chunks=((1, 2), (9,), (4, 5, 6))
        )
        self.assertEqual(d.npartitions, 6)
        self.assertEqual(
            list(d.chunk_indices()),
            [
                (slice(0, 1, None), slice(0, 9, None), slice(0, 4, None)),
                (slice(0, 1, None), slice(0, 9, None), slice(4, 9, None)),
                (slice(0, 1, None), slice(0, 9, None), slice(9, 15, None)),
                (slice(1, 3, None), slice(0, 9, None), slice(0, 4, None)),
                (slice(1, 3, None), slice(0, 9, None), slice(4, 9, None)),
                (slice(1, 3, None), slice(0, 9, None), slice(9, 15, None)),
            ],
        )

    def test_Data_chunk_positions(self):
        """Test Data.chunk_positions."""
        d = cfdm.Data(
            np.arange(60).reshape(3, 4, 5), chunks=((1, 2), (4,), (1, 2, 2))
        )
        self.assertEqual(d.npartitions, 6)
        self.assertEqual(
            list(d.chunk_positions()),
            [(0, 0, 0), (0, 0, 1), (0, 0, 2), (1, 0, 0), (1, 0, 1), (1, 0, 2)],
        )

    def test_Data_dataset_chunksizes(self):
        """Test Data.nc_dataset_chunksizes."""
        d = cfdm.Data(np.arange(24).reshape(2, 3, 4))
        self.assertIsNone(d.nc_dataset_chunksizes())
        self.assertIsNone(d.nc_set_dataset_chunksizes([2, 2, 2]))
        self.assertEqual(d.nc_dataset_chunksizes(), (2, 2, 2))
        self.assertEqual(d.nc_clear_dataset_chunksizes(), (2, 2, 2))
        self.assertIsNone(d.nc_dataset_chunksizes())

        self.assertIsNone(d.nc_set_dataset_chunksizes("contiguous"))
        self.assertEqual(d.nc_dataset_chunksizes(), "contiguous")
        self.assertEqual(d.nc_clear_dataset_chunksizes(), "contiguous")
        self.assertIsNone(d.nc_dataset_chunksizes())

        self.assertIsNone(d.nc_set_dataset_chunksizes(None))
        self.assertIsNone(d.nc_dataset_chunksizes())

        d.nc_clear_dataset_chunksizes()
        d.nc_set_dataset_chunksizes({1: 2})
        self.assertEqual(d.nc_dataset_chunksizes(), (2, 2, 4))
        d.nc_set_dataset_chunksizes({0: 1, 2: 3})
        self.assertEqual(d.nc_dataset_chunksizes(), (1, 2, 3))

        for chunksizes in (1024, "1 KiB"):
            self.assertIsNone(d.nc_set_dataset_chunksizes(chunksizes))
            self.assertEqual(d.nc_clear_dataset_chunksizes(), 1024)

        # Bad chunk sizes
        for chunksizes in (
            [2],
            [-99, 3, 4],
            [2, 3, 3.14],
            [2, "bad", 4],
            "bad",
            {2: 3.14},
        ):
            with self.assertRaises(ValueError):
                d.nc_set_dataset_chunksizes(chunksizes)

        # todict
        d.nc_set_dataset_chunksizes([2, 3, 4])
        self.assertEqual(
            d.nc_dataset_chunksizes(todict=True), {0: 2, 1: 3, 2: 4}
        )

        for chunksizes in (None, "contiguous", 1024):
            d.nc_set_dataset_chunksizes(chunksizes)
            with self.assertRaises(ValueError):
                d.nc_dataset_chunksizes(todict=True)

        # full axis size
        d.nc_set_dataset_chunksizes([-1, None, 999])
        self.assertEqual(d.nc_dataset_chunksizes(), d.shape)

    def test_Data_masked_where(self):
        """Test Data.masked_where."""
        array = np.array([[1, 2, 3], [4, 5, 6]])
        d = cfdm.Data(array)
        mask = [[0, 1, 0], [1, 0, 0]]
        e = d.masked_where(mask)
        ea = e.array
        a = np.ma.masked_where(mask, array)
        self.assertTrue((ea == a).all())
        self.assertTrue((ea.mask == a.mask).all())
        self.assertIsNone(d.masked_where(mask, inplace=True))
        self.assertTrue(d.equals(e))

    def test_Data_all(self):
        """Test Data.all."""
        d = cfdm.Data([[1, 2], [3, 4]], "m")
        self.assertTrue(d.all())
        self.assertEqual(d.all(keepdims=False).shape, ())
        self.assertEqual(d.all(axis=()).shape, d.shape)
        self.assertTrue((d.all(axis=0).array == [True, True]).all())
        self.assertTrue((d.all(axis=1).array == [True, True]).all())
        self.assertEqual(d.all().Units, cfdm.Units())

        d[0] = cfdm.masked
        d[1, 0] = 0
        self.assertTrue((d.all(axis=0).array == [False, True]).all())
        self.assertTrue(
            (
                d.all(axis=1).array == np.ma.array([True, False], mask=[1, 0])
            ).all()
        )

        d[...] = cfdm.masked
        self.assertTrue(d.all())
        self.assertFalse(d.all(keepdims=False))

    def test_Data_concatenate(self):
        """Test Data.concatenate."""
        # Unitless operation with default axis (axis=0):
        d_np = np.arange(120).reshape(30, 4)
        e_np = np.arange(120, 280).reshape(40, 4)
        d = cfdm.Data(d_np)
        e = cfdm.Data(e_np)
        f_np = np.concatenate((d_np, e_np), axis=0)
        f = cfdm.Data.concatenate((d, e))
        self.assertEqual(f.shape, f_np.shape)
        self.assertTrue((f.array == f_np).all())

        d_np = np.array([[1, 2], [3, 4]])
        e_np = np.array([[5.0, 6.0]])
        d = cfdm.Data(d_np, "km")
        e = cfdm.Data(e_np, "km")
        f_np = np.concatenate((d_np, e_np), axis=0)
        f = cfdm.Data.concatenate([d, e])
        self.assertEqual(f.shape, f_np.shape)
        self.assertTrue((f.array == f_np).all())

        # Check axes equivalency:
        self.assertTrue(f.equals(cfdm.Data.concatenate((d, e), axis=-2)))

        # Non-default axis specification:
        e_np = np.array([[5.0], [6.0]])  # for compatible shapes with axis=1
        e = cfdm.Data(e_np, "km")
        f_np = np.concatenate((d_np, e_np), axis=1)
        f = cfdm.Data.concatenate((d, e), axis=1)
        self.assertEqual(f.shape, f_np.shape)
        self.assertTrue((f.array == f_np).all())

        # Operation with every data item in sequence being a scalar:
        d_np = np.array(1)
        e_np = np.array(50.0)
        d = cfdm.Data(d_np, "km")
        e = cfdm.Data(e_np, "km")

        # Note can't use the following (to compute answer):
        #     f_np = np.concatenate([d_np, e_np])
        # here since we have different behaviour to NumPy w.r.t
        # scalars, where NumPy would error for the above with:
        #     ValueError: zero-dimensional arrays cannot be concatenated
        f_answer = np.array([d_np, e_np])
        f = cfdm.Data.concatenate((d, e))
        self.assertEqual(f.shape, f_answer.shape)
        self.assertTrue((f.array == f_answer).all())

        # Operation with some scalar and some non-scalar data in the
        # sequence:
        e_np = np.array([50.0, 75.0])
        e = cfdm.Data(e_np, "km")

        # As per above comment, can't use np.concatenate to compute
        f_answer = np.array([1.0, 50, 75])
        f = cfdm.Data.concatenate((d, e))
        self.assertEqual(f.shape, f_answer.shape)
        self.assertTrue((f.array == f_answer).all())

        # Check cached elements
        cached = f._get_cached_elements()
        self.assertEqual(cached[0], d.first_element())
        self.assertEqual(cached[-1], e.last_element())

        # Check concatenation with one invalid units
        d.Units = cfdm.Units("foo")
        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e], relaxed_units=True)

        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e], axis=1)

        # Check concatenation with both invalid units
        d.Units = cfdm.Units("foo")
        e.Units = cfdm.Units("foo")
        f = cfdm.Data.concatenate([d, e], relaxed_units=True)
        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e])

        e.Units = cfdm.Units("foobar")
        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e], relaxed_units=True)

        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e])

        e.Units = cfdm.Units("metre")
        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e], relaxed_units=True)

        with self.assertRaises(ValueError):
            f = cfdm.Data.concatenate([d, e], axis=1)

        # Test cached elements
        d = cfdm.Data([1, 2, 3])
        e = cfdm.Data([4, 5])
        repr(d)
        repr(e)
        f = cfdm.Data.concatenate([d, e], axis=0)
        self.assertEqual(
            f._get_cached_elements(),
            {0: d.first_element(), -1: e.last_element()},
        )

    def test_Data_aggregated_data(self):
        """Test Data aggregated_data methods."""
        d = cfdm.Data(9)
        aggregated_data = {
            "location": "location",
            "shape": "shape",
            "address": "cfa_address",
        }

        self.assertFalse(d.nc_has_aggregated_data())
        self.assertIsNone(d.nc_set_aggregated_data(aggregated_data))
        self.assertTrue(d.nc_has_aggregated_data())
        self.assertEqual(d.nc_get_aggregated_data(), aggregated_data)
        self.assertEqual(d.nc_del_aggregated_data(), aggregated_data)
        self.assertFalse(d.nc_has_aggregated_data())
        self.assertEqual(d.nc_get_aggregated_data(), {})
        self.assertEqual(d.nc_del_aggregated_data(), {})

    def test_Data_replace_directory(self):
        """Test Data.replace_directory."""
        f = self.f0

        # No files means no stored directories
        self.assertEqual(f.data.file_directories(), set())

        cfdm.write(f, file_A)
        d = cfdm.read(file_A, dask_chunks=4)[0].data
        self.assertGreater(d.npartitions, 1)

        e = d.copy()
        directory = cfdm.dirname(file_A)

        self.assertEqual(d.file_directories(), set([directory]))
        self.assertIsNone(d.replace_directory())
        d.replace_directory(directory, "/new/path")
        self.assertEqual(
            d.file_directories(),
            set(["/new/path"]),
        )
        self.assertEqual(
            d.get_filenames(), set((f"/new/path/{os.path.basename(file_A)}",))
        )

        # Check that we haven't changed 'e'
        self.assertEqual(e.file_directories(), set([directory]))

        d.replace_directory(new="/newer/path", common=True)
        self.assertEqual(
            d.file_directories(),
            set(["/newer/path"]),
        )
        self.assertEqual(
            d.get_filenames(),
            set((f"/newer/path/{os.path.basename(file_A)}",)),
        )

        with self.assertRaises(ValueError):
            d.replace_directory(old="something", common=True)

        d.replace_directory("/newer/path")
        self.assertEqual(
            d.file_directories(),
            set([""]),
        )
        self.assertEqual(
            d.get_filenames(), set((f"{os.path.basename(file_A)}",))
        )

    def test_Data_replace_filenames(self):
        """Test Data.replace_filenames."""
        f = self.f0
        cfdm.write(f[:2], file_A)
        cfdm.write(f[2:], file_B)
        a = cfdm.read(file_A)[0]
        b = cfdm.read(file_B)[0]
        d = cfdm.Data.concatenate([a.data, b.data], axis=0)

        self.assertEqual(d.get_filenames(), set([file_A, file_B]))
        self.assertEqual(d.numblocks, (2, 1))

        new_filenames = [["a"], ["b"]]
        self.assertIsNone(d.replace_filenames(new_filenames))
        self.assertEqual(d.numblocks, np.shape(new_filenames))

        self.assertEqual(d.get_filenames(normalise=False), set(["a", "b"]))
        self.assertTrue(
            (
                d.get_filenames(normalise=False, per_chunk=True)
                == new_filenames
            ).all()
        )

    def test_Data_has_deterministic_name(self):
        """Test Data.has_deterministic_name."""
        d = cfdm.Data([1, 2], "m")
        e = cfdm.Data([4, 5], "km")
        self.assertTrue(d.has_deterministic_name())
        self.assertTrue(e.has_deterministic_name())

        d._update_deterministic(False)
        self.assertFalse(d.has_deterministic_name())

    def test_Data_get_deterministic_name(self):
        """Test Data.get_deterministic_name."""
        d = cfdm.Data([1, 2], "m")
        e = d.copy()
        e.Units = cfdm.Units("metre")
        self.assertEqual(
            e.get_deterministic_name(), d.get_deterministic_name()
        )

        d._update_deterministic(False)
        with self.assertRaises(ValueError):
            d.get_deterministic_name()

    def test_Data__data__(self):
        """Test Data.__data__."""
        d = cfdm.Data([1, 2, 3], "m")
        self.assertIs(d, d.__data__())

    def test_Data_asdata(self):
        """Test Data.asdata."""
        d = cfdm.Data([1, 2, 3], "m")

        self.assertIs(d.asdata(d), d)
        self.assertIs(cfdm.Data.asdata(d), d)
        self.assertIs(d.asdata(d, dtype=d.dtype), d)
        self.assertIs(cfdm.Data.asdata(d, dtype=d.dtype), d)

        self.assertIsNot(d.asdata(d, dtype="float32"), d)
        self.assertIsNot(cfdm.Data.asdata(d, dtype="float32"), d)
        self.assertIsNot(d.asdata(d, dtype=d.dtype, copy=True), d)
        self.assertIsNot(cfdm.Data.asdata(d, dtype=d.dtype, copy=True), d)

        self.assertTrue(
            cfdm.Data.asdata(
                cfdm.Data([1, 2, 3]), dtype=float, copy=True
            ).equals(cfdm.Data([1.0, 2, 3]), verbose=2)
        )

        self.assertTrue(
            cfdm.Data.asdata([1, 2, 3]).equals(cfdm.Data([1, 2, 3]), verbose=2)
        )
        self.assertTrue(
            cfdm.Data.asdata([1, 2, 3], dtype=float).equals(
                cfdm.Data([1.0, 2, 3]), verbose=2
            )
        )

    def test_Data_full(self):
        """Test Data.full."""
        fill_value = 999
        for shape, dtype_in, dtype_out in zip(
            [(), (2,), (4, 5)], [None, float, bool], [int, float, bool]
        ):
            d = cfdm.Data.full(shape, fill_value, dtype=dtype_in, chunks=-1)
            self.assertEqual(d.shape, shape)
            self.assertEqual(d.dtype, dtype_out)
            self.assertTrue(
                (d.array == np.full(shape, fill_value, dtype=dtype_in)).all()
            )

    def test_Data_ones(self):
        """Test Data.ones."""
        for shape, dtype_in, dtype_out in zip(
            [(), (3,), (4, 5)], [None, int, bool], [float, int, bool]
        ):
            d = cfdm.Data.ones(shape, dtype=dtype_in, chunks=-1)
            self.assertEqual(d.shape, shape)
            self.assertEqual(d.dtype, dtype_out)
            self.assertTrue((d.array == np.ones(shape, dtype=dtype_in)).all())

    def test_Data_zeros(self):
        """Test Data.zeros."""
        for shape, dtype_in, dtype_out in zip(
            [(), (3,), (4, 5)], [None, int, bool], [float, int, bool]
        ):
            d = cfdm.Data.zeros(shape, dtype=dtype_in, chunks=-1)
            self.assertEqual(d.shape, shape)
            self.assertEqual(d.dtype, dtype_out)
            self.assertTrue((d.array == np.zeros(shape, dtype=dtype_in)).all())

    def test_Data_dtype(self):
        """Test Data.dtype."""
        d = cfdm.Data([[280, 278, -99, -99]], mask=[[0, 0, 1, 1]], dtype=float)
        self.assertTrue(d.dtype, "float64")

        _ = repr(d)
        cache0 = d._get_cached_elements().copy()
        self.assertTrue(cache0)

        for a in cache0.values():
            if a is not np.ma.masked:
                self.assertEqual(a.dtype, d.dtype)

        d.dtype = "float32"
        self.assertTrue(d.dtype, "float32")

        cache1 = d._get_cached_elements().copy()
        self.assertTrue(cache1)
        self.assertEqual(cache0, cache1)

        for a in cache1.values():
            if a is not np.ma.masked:
                self.assertEqual(a.dtype, d.dtype)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
