import datetime
import faulthandler
import unittest

import cftime
import dask.array as da
import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DataUtilsTest(unittest.TestCase):
    """Test `Data` utility functions."""

    def test_Data_utils_allclose(self):
        """Test allclose."""
        # Create a range of inputs to test against.  Note that 'a' and
        # 'a2' should be treated as 'allclose' for this method, the
        # same result as np.ma.allclose would give because all of the
        # *unmasked* elements are 'allclose', whereas in our
        # Data.equals method that builds on this method, we go even
        # further and insist on the mask being identical as well as
        # the data (separately, i.e. unmasked) all being 'allclose',
        # so inside our cfdm.Data objects 'a' and 'a2' would instead
        # *not* be considered equal.
        a_np = np.ma.array([1.0, 2.0, 3.0], mask=[1, 0, 0])
        a = da.from_array(a_np)
        a2 = da.from_array(np.ma.array([10.0, 2.0, 3.0], mask=[1, 0, 0]))
        b_np = np.ma.array([1.0, 2.0, 3.0], mask=[0, 1, 0])
        b = da.from_array(b_np)
        c_np = np.ma.array([1.0, 2.0, 100.0], mask=[1, 0, 0])
        c = da.from_array(c_np)
        d = da.from_array(np.array([1.0, 2.0, 3.0]))
        e = a + 5e-04  # outside of tolerance to set, namely rtol=1e-05
        f = a + 5e-06  # within set tolerance to be specified, as above

        # Test the function with these inputs as both numpy and dask
        # arrays...
        allclose = cfdm.data.utils.allclose

        atol = cfdm.atol()
        rtol = cfdm.rtol()
        tol = {"atol": atol, "rtol": rtol}

        self.assertTrue(allclose(a, a, **tol).compute())
        self.assertTrue(allclose(a2, a, **tol).compute())
        self.assertTrue(allclose(b, a, **tol).compute())

        # ...including testing the 'masked_equal' parameter
        self.assertFalse(allclose(b, a, masked_equal=False, **tol).compute())

        self.assertFalse(allclose(c, a, **tol).compute())
        self.assertTrue(allclose(d, a, **tol).compute())
        self.assertFalse(allclose(e, a, **tol).compute())

        self.assertTrue(allclose(f, a, atol=atol, rtol=1e-05).compute())

        # Test when array inputs have different chunk sizes
        a_chunked = da.from_array(a_np, chunks=(1, 2))
        self.assertTrue(
            allclose(
                da.from_array(b_np, chunks=(3,)), a_chunked, **tol
            ).compute()
        )
        self.assertFalse(
            allclose(
                da.from_array(b_np, chunks=(3,)),
                a_chunked,
                masked_equal=False,
                **tol
            ).compute()
        )
        self.assertFalse(
            allclose(
                da.from_array(c_np, chunks=(3,)), a_chunked, **tol
            ).compute()
        )

        # Test the 'rtol' and 'atol' parameters:
        self.assertFalse(allclose(e, a, atol=atol, rtol=1e-06).compute())
        b1 = e / 10000
        b2 = a / 10000
        self.assertTrue(allclose(b1, b2, atol=1e-05, rtol=rtol).compute())

    def test_Data_utils_is_numeric_dtype(self):
        """Test is_numeric_dtype."""
        is_numeric_dtype = cfdm.data.utils.is_numeric_dtype
        for a in [
            np.array([0, 1, 2]),
            np.array([False, True, True]),
            np.ma.array([10.0, 2.0, 3.0], mask=[1, 0, 0]),
            np.array(10),
        ]:
            self.assertTrue(is_numeric_dtype(a))

        for b in [
            np.array(["a", "b", "c"], dtype="S1"),
            np.empty(1, dtype=object),
        ]:
            self.assertFalse(is_numeric_dtype(b))

    def test_Data_utils_convert_to_datetime(self):
        """Test convert_to_datetime."""
        a = cftime.DatetimeGregorian(2000, 12, 3, 12)
        for x in (2.5, [2.5]):
            d = da.from_array(x)
            e = cfdm.data.utils.convert_to_datetime(
                d, cfdm.Units("days since 2000-12-01")
            )
            self.assertEqual(e.compute(), a)

        a = [
            cftime.DatetimeGregorian(2000, 12, 1),
            cftime.DatetimeGregorian(2000, 12, 2),
            cftime.DatetimeGregorian(2000, 12, 3),
        ]
        for x in ([0, 1, 2], [[0, 1, 2]]):
            d = da.from_array([0, 1, 2], chunks=2)
            e = cfdm.data.utils.convert_to_datetime(
                d, cfdm.Units("days since 2000-12-01")
            )
            self.assertTrue((e.compute() == a).all())

    def test_Data_utils_convert_to_reftime(self):
        """Test convert_to_reftime."""
        a = cftime.DatetimeGregorian(2000, 12, 3, 12)
        d = da.from_array(np.array(a, dtype=object))

        e, u = cfdm.data.utils.convert_to_reftime(d)
        self.assertEqual(e.compute(), 0.5)
        self.assertEqual(u, cfdm.Units("days since 2000-12-03", "standard"))

        units = cfdm.Units("days since 2000-12-01")
        e, u = cfdm.data.utils.convert_to_reftime(d, units=units)
        self.assertEqual(e.compute(), 2.5)
        self.assertEqual(u, units)

        a = "2000-12-03T12:00"
        d = da.from_array(np.array(a, dtype=str))

        e, u = cfdm.data.utils.convert_to_reftime(d)
        self.assertEqual(e.compute(), 0.5)
        self.assertEqual(u, cfdm.Units("days since 2000-12-03", "standard"))

        units = cfdm.Units("days since 2000-12-01")
        e, u = cfdm.data.utils.convert_to_reftime(d, units=units)
        self.assertEqual(e.compute(), 2.5)
        self.assertEqual(u, units)

        a = [
            [
                cftime.DatetimeGregorian(2000, 12, 1),
                cftime.DatetimeGregorian(2000, 12, 2),
                cftime.DatetimeGregorian(2000, 12, 3),
            ]
        ]
        d = da.from_array(np.ma.array(a, mask=[[1, 0, 0]]), chunks=2)

        e, u = cfdm.data.utils.convert_to_reftime(d)
        self.assertTrue((e.compute() == [-99, 0, 1]).all())
        self.assertEqual(u, cfdm.Units("days since 2000-12-02", "standard"))

        units = cfdm.Units("days since 2000-12-03")
        e, u = cfdm.data.utils.convert_to_reftime(d, units=units)
        self.assertTrue((e.compute() == [-99, -1, 0]).all())
        self.assertEqual(u, units)

        d = cfdm.Data(
            ["2004-02-29", "2004-02-30", "2004-03-01"], calendar="360_day"
        )
        self.assertEqual(
            d.Units, cfdm.Units("days since 2004-02-29", "360_day")
        )
        self.assertTrue((d.array == [0, 1, 2]).all())

        d = cfdm.Data(["2004-02-29", "2004-03-01"], dt=True)
        self.assertEqual(d.Units, cfdm.Units("days since 2004-02-29"))
        self.assertTrue((d.array == [0, 1]).all())

    def test_Data_utils_first_non_missing_value(self):
        """Test first_non_missing_value."""
        for method in ("index", "mask"):
            # Scalar data
            d = da.from_array(0)
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), 0
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            d[()] = np.ma.masked
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), None
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            # 1-d data
            d = da.arange(8)
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), 0
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            d[0] = np.ma.masked
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), 1
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            # 2-d data
            d = da.arange(8).reshape(2, 4)
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), 0
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            d[0] = np.ma.masked
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), 4
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

            d[...] = np.ma.masked
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(d, method=method), None
            )
            self.assertEqual(
                cfdm.data.utils.first_non_missing_value(
                    d, cached=99, method=method
                ),
                99,
            )

        # Bad method
        with self.assertRaises(ValueError):
            cfdm.data.utils.first_non_missing_value(d, method="bad")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
