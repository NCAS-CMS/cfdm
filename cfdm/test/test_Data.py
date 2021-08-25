import copy
import datetime
import faulthandler
import itertools
import os
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


def axes_combinations(ndim):
    """Create axes permutations for `test_Data_flatten`."""
    return [
        axes
        for n in range(1, ndim + 1)
        for axes in itertools.permutations(range(ndim), n)
    ]


class DataTest(unittest.TestCase):
    """Unit test for the Data class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

    def test_Data_any(self):
        """Test the any Data method."""
        d = cfdm.Data([[0, 0, 0]])
        self.assertFalse(d.any())
        d[0, 0] = numpy.ma.masked
        self.assertFalse(d.any())
        d[0, 1] = 3
        self.assertTrue(d.any())
        d[...] = numpy.ma.masked
        self.assertFalse(d.any())

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

    #    def test_Data__getitem__(self):
    def test_Data__setitem__(self):
        """Test the assignment of data items on Data."""
        a = numpy.ma.arange(3000).reshape(50, 60)

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
                (cfdm.masked, numpy.ma.masked),
                (n, n),
            ):
                message = f"cfdm.Data[{j}, {i}]={dvalue}={avalue} failed"
                d[j, i] = dvalue
                a[j, i] = avalue
                x = d.array
                self.assertTrue(
                    (x == a).all() in (True, numpy.ma.masked), message
                )
                m = numpy.ma.getmaskarray(x)
                self.assertTrue(
                    (m == numpy.ma.getmaskarray(a)).all(),
                    "d.mask.array="
                    + repr(m)
                    + "\nnumpy.ma.getmaskarray(a)="
                    + repr(numpy.ma.getmaskarray(a)),
                )

        a = numpy.ma.arange(3000).reshape(50, 60)

        d = cfdm.Data(a.filled(), "m")

        (j, i) = (slice(0, 2), slice(0, 3))
        array = numpy.array([[1, 2, 6], [3, 4, 5]]) * -1

        for dvalue in (array, numpy.ma.masked_where(array < -2, array), array):
            message = "cfdm.Data[%s, %s]=%s failed" % (j, i, dvalue)
            d[j, i] = dvalue
            a[j, i] = dvalue
            x = d.array
            self.assertTrue((x == a).all() in (True, numpy.ma.masked), message)
            m = numpy.ma.getmaskarray(x)
            self.assertTrue((m == numpy.ma.getmaskarray(a)).all(), message)

        # Scalar numeric array
        d = cfdm.Data(9, units="km")
        d[...] = cfdm.masked
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], numpy.ma.masked)

    def test_Data_apply_masking(self):
        """Test the `apply_masking` Data method."""
        a = numpy.ma.arange(12).reshape(3, 4)
        a[1, 1] = numpy.ma.masked

        d = cfdm.Data(a, units="m")

        self.assertTrue((a == d.array).all())
        self.assertTrue((a.mask == d.mask.array).all())

        b = a.copy()
        e = d.apply_masking()
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a == 0, numpy.ma.masked, a)
        e = d.apply_masking(fill_values=[0])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a == 0) | (a == 11), numpy.ma.masked, a)
        e = d.apply_masking(fill_values=[0, 11])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a < 3, numpy.ma.masked, a)
        e = d.apply_masking(valid_min=3)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a > 6, numpy.ma.masked, a)
        e = d.apply_masking(valid_max=6)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a < 2) | (a > 8), numpy.ma.masked, a)
        e = d.apply_masking(valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        d.set_fill_value(7)

        b = numpy.ma.where(a == 7, numpy.ma.masked, a)
        e = d.apply_masking(fill_values=True)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a == 7) | (a < 2) | (a > 8), numpy.ma.masked, a)
        e = d.apply_masking(fill_values=True, valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

    #    def test_Data_astype(self):
    #        a = numpy.array([1.5, 2, 2.5], dtype=float)
    #        d = cfdm.Data(a)
    #
    #        self.assertTrue(d.dtype == numpy.dtype(float))
    #        self.assertTrue(d.array.dtype == numpy.dtype(float))
    #        self.assertTrue((d.array == a).all())
    #
    #        d.astype('int32')
    #        self.assertTrue(d.dtype == numpy.dtype('int32'))
    #        self.assertTrue(d.array.dtype == numpy.dtype('int32'))
    #        self.assertTrue((d.array == [1, 2, 2]).all())
    #
    #        d = cfdm.Data(a)
    #        try:
    #            d.astype(numpy.dtype(int, casting='safe'))
    #            self.assertTrue(False)
    #        except TypeError:
    #            pass

    def test_Data_array(self):
        """Test the array Data method."""
        # ------------------------------------------------------------
        # Numpy array interface (__array__)
        # ------------------------------------------------------------
        a = numpy.arange(12, dtype="int32").reshape(3, 4)

        d = cfdm.Data(a, units="km")

        b = numpy.array(d)

        self.assertEqual(b.dtype, numpy.dtype("int32"))
        self.assertEqual(a.shape, b.shape)
        self.assertTrue((a == b).all())

        b = numpy.array(d, dtype="float32")

        self.assertEqual(b.dtype, numpy.dtype("float32"))
        self.assertEqual(a.shape, b.shape)
        self.assertTrue((a == b).all())

        # Scalar numeric array
        d = cfdm.Data(9, units="km")
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertEqual(a, numpy.array(9))
        d[...] = cfdm.masked
        a = d.array
        self.assertEqual(a.shape, ())
        self.assertIs(a[()], numpy.ma.masked)

        # Non-scalar numeric array
        b = numpy.arange(10 * 15 * 19).reshape(10, 1, 15, 19)
        d = cfdm.Data(b, "km")
        a = d.array
        a[0, 0, 0, 0] = -999
        a2 = d.array
        self.assertEqual(a2[0, 0, 0, 0], 0)
        self.assertEqual(a2.shape, b.shape)
        self.assertTrue((a2 == b).all())
        self.assertFalse((a2 == a).all())

    def test_Data_datetime_array(self):
        """Test the `datetime_array` Data method."""
        d = cfdm.Data([11292.5, 11293], units="days since 1970-1-1")
        dt = d.datetime_array
        self.assertEqual(dt[0], datetime.datetime(2000, 12, 1, 12, 0))
        self.assertEqual(dt[1], datetime.datetime(2000, 12, 2, 0, 0))

        d[0] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[0], numpy.ma.masked)
        self.assertEqual(dt[1], datetime.datetime(2000, 12, 2, 0, 0))

        d = cfdm.Data(11292.5, units="days since 1970-1-1")
        dt = d.datetime_array
        self.assertEqual(dt[()], datetime.datetime(2000, 12, 1, 12, 0))

        d[()] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[()], numpy.ma.masked)

    def test_Data_flatten(self):
        """Test the flatten Data method."""
        ma = numpy.ma.arange(24).reshape(1, 2, 3, 4)
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

        for axes in axes_combinations(d.ndim):
            e = d.flatten(axes)

            if len(axes) <= 1:
                shape = d.shape
            else:
                shape = [n for i, n in enumerate(d.shape) if i not in axes]
                shape.insert(
                    sorted(axes)[0],
                    numpy.prod(
                        [n for i, n in enumerate(d.shape) if i in axes]
                    ),
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
        """Test the transpose Data method."""
        a = numpy.arange(2 * 3 * 5).reshape(2, 1, 3, 5)
        d = cfdm.Data(a.copy())

        for indices in (list(range(a.ndim)), list(range(-a.ndim, 0))):
            for axes in itertools.permutations(indices):
                a = numpy.transpose(a, axes)
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

    def test_Data_unique(self):
        """Test the unique Data method."""
        d = cfdm.Data([[4, 2, 1], [1, 2, 3]], units="metre")
        u = d.unique()
        self.assertEqual(u.shape, (4,))
        self.assertTrue(
            (u.array == cfdm.Data([1, 2, 3, 4], "metre").array).all()
        )

        d[1, -1] = cfdm.masked
        u = d.unique()
        self.assertEqual(u.shape, (3,))
        self.assertTrue((u.array == cfdm.Data([1, 2, 4], "metre").array).all())

    def test_Data_equals(self):
        """Test the equality-testing Data method."""
        a = numpy.ma.arange(10 * 15 * 19).reshape(10, 1, 15, 19)
        a[0, 0, 2, 3] = numpy.ma.masked

        d = cfdm.Data(a, units="days since 2000-2-2", calendar="noleap")
        e = copy.deepcopy(d)

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

    def test_Data_maximum_minimum_sum_squeeze(self):
        """Test the maximum, minimum, sum and squeeze Data methods."""
        a = numpy.ma.arange(2 * 3 * 5).reshape(2, 1, 3, 5)
        a[0, 0, 0, 0] = numpy.ma.masked
        a[-1, -1, -1, -1] = numpy.ma.masked
        a[1, -1, 1, 3] = numpy.ma.masked
        d = cfdm.Data(a)

        b = a.max()
        x = d.maximum().squeeze()
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=0)
        x = d.maximum(axes=0).squeeze(0)
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=(0, 3))
        x = d.maximum(axes=[0, 3]).squeeze([0, 3])
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())
        self.assertTrue(d.maximum([0, 3]).equals(d.max([0, 3])))

        b = a.min()
        x = d.minimum().squeeze()
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min(axis=(0, 3))
        x = d.minimum(axes=[0, 3]).squeeze([0, 3])
        self.assertEqual(x.shape, b.shape)
        self.assertTrue((x.array == b).all(), (x.shape, b.shape))
        self.assertTrue(d.minimum([0, 3]).equals(d.min([0, 3])))

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
            d.maximum(axes=99)

        with self.assertRaises(ValueError):
            d.minimum(axes=99)

        d = cfdm.Data(9)
        self.assertTrue(d.equals(d.squeeze()))

        with self.assertRaises(ValueError):
            d.sum(axes=0)

        with self.assertRaises(ValueError):
            d.squeeze(axes=0)

        with self.assertRaises(ValueError):
            d.minimum(axes=0)

        with self.assertRaises(ValueError):
            d.maximum(axes=0)

    def test_Data_dtype_mask(self):
        """Test the dtype and mask Data methods."""
        a = numpy.ma.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        d = cfdm.Data([[280, -99, -99, -99], [281, 279, 278, 279]])
        self.assertEqual(d.dtype, numpy.dtype(int))

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]],
            dtype=float,
            mask=[[0, 1, 1, 1], [0, 0, 0, 0]],
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertTrue((d.array == a).all())
        self.assertEqual(d.mask.shape, a.mask.shape)
        self.assertTrue((d.mask.array == numpy.ma.getmaskarray(a)).all())

        a = numpy.array(
            [[280.0, -99, -99, -99], [281.0, 279.0, 278.0, 279.0]], dtype=float
        )
        mask = numpy.ma.masked_all(a.shape).mask

        d = cfdm.Data(
            [[280, -99, -99, -99], [281, 279, 278, 279]], dtype=float
        )

        self.assertEqual(d.dtype, a.dtype)
        self.assertTrue((d.array == a).all())
        self.assertEqual(d.mask.shape, mask.shape)
        self.assertTrue((d.mask.array == numpy.ma.getmaskarray(a)).all())

    def test_Data_get_index(self):
        """Test the `get_index` Data method."""
        d = cfdm.Data([[281, 279, 278, 279]])
        self.assertIsNone(d.get_index(default=None))

    def test_Data_get_list(self):
        """Test the `get_list` Data method."""
        d = cfdm.Data([[281, 279, 278, 279]])
        self.assertIsNone(d.get_list(default=None))

    def test_Data_get_count(self):
        """Test the `get_count` Data method."""
        d = cfdm.Data([[281, 279, 278, 279]])
        self.assertIsNone(d.get_count(default=None))

    def test_Data_filled(self):
        """Test the filled Data method."""
        d = cfdm.Data([[1, 2, 3]])
        self.assertTrue((d.filled().array == [[1, 2, 3]]).all())

        d[0, 0] = cfdm.masked
        self.assertTrue(
            (
                d.filled().array
                == [
                    [
                        -9223372036854775806,
                        2,
                        3,
                    ]
                ]
            ).all()
        )

        d.set_fill_value(-99)
        self.assertTrue(
            (
                d.filled().array
                == [
                    [
                        -99,
                        2,
                        3,
                    ]
                ]
            ).all()
        )

        self.assertTrue(
            (
                d.filled(1e10).array
                == [
                    [
                        1e10,
                        2,
                        3,
                    ]
                ]
            ).all()
        )

        d = cfdm.Data(["a", "b", "c"], mask=[1, 0, 0])
        self.assertTrue((d.filled().array == ["", "b", "c"]).all())

    def test_Data_insert_dimension(self):
        """Test the `insert_dimension` Data method."""
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
        self.assertEqual(
            e.shape,
            (
                1,
                12,
            ),
        )
        self.assertIsNone(e.squeeze(0, inplace=True))
        self.assertEqual(e.shape, (12,))

        d = e
        d.insert_dimension(0, inplace=True)
        d.insert_dimension(-1, inplace=True)
        d.insert_dimension(-1, inplace=True)
        self.assertEqual(d.shape, (1, 12, 1, 1))
        e = d.squeeze([0, 2])
        self.assertEqual(e.shape, (12, 1))

        array = numpy.arange(12).reshape(1, 4, 3)
        d = cfdm.Data(array)
        e = d.squeeze()
        f = e.insert_dimension(0)
        a = f.array
        self.assertTrue(numpy.allclose(a, array))

        with self.assertRaises(ValueError):
            d.insert_dimension(1000)

    def test_Data_get_compressed_dimension(self):
        """Test the `get_compressed_dimension` Data method."""
        d = cfdm.Data([[281, 279, 278, 279]])
        self.assertIsNone(d.get_compressed_dimension(None))

    def test_Data__format__(self):
        """Test the `__format__` Data method."""
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


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
