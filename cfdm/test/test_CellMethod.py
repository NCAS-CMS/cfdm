import datetime
import faulthandler
import os
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class CellMethodTest(unittest.TestCase):
    """Unit test for the CellMethod class."""

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
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, f"f={f!r}")
        self.f = f[0]

    def test_CellMethod__repr__str__dump_construct_type(self):
        """Test all means of CellMethod inspection."""
        f = self.f

        for c in f.cell_methods().values():
            _ = repr(c)
            _ = str(c)
            self.assertIsInstance(c.dump(display=False), str)
            self.assertEqual(c.construct_type, "cell_method")

    def test_CellMethod(self):
        """Test CellMethod equality, identity and sorting methods."""
        f = self.f

        # ------------------------------------------------------------
        # Equals and identities
        # ------------------------------------------------------------
        for c in f.cell_methods().values():
            d = c.copy()
            self.assertTrue(c.equals(c, verbose=3))
            self.assertTrue(c.equals(d, verbose=3))
            self.assertTrue(d.equals(c, verbose=3))
            self.assertEqual(c.identity(), "method:" + c.get_method())
            self.assertEqual(c.identities(), ["method:" + c.get_method()])

        # ------------------------------------------------------------
        # Sorted
        # ------------------------------------------------------------
        c = cfdm.CellMethod(
            method="minimum", axes=["B", "A"], qualifiers={"interval": [1, 2]}
        )

        d = cfdm.CellMethod(
            method="minimum", axes=["A", "B"], qualifiers={"interval": [2, 1]}
        )

        self.assertTrue(d.equals(c.sorted(), verbose=3))

        c = cfdm.CellMethod(
            method="minimum", axes=["B", "A"], qualifiers={"interval": [3]}
        )

        d = cfdm.CellMethod(
            method="minimum", axes=["A", "B"], qualifiers={"interval": [3]}
        )

        self.assertTrue(d.equals(c.sorted(), verbose=3))

        c = cfdm.CellMethod(
            method="minimum", axes=["area"], qualifiers={"interval": [3]}
        )

        d = cfdm.CellMethod(
            method="minimum", axes=["area"], qualifiers={"interval": [3]}
        )

        self.assertTrue(d.equals(c.sorted(), verbose=3))

        # Init
        c = cfdm.CellMethod(source="qwerty")

    def test_CellMethod_axes(self):
        """Test the axes access and (un)setting CellMethod methods."""
        f = cfdm.CellMethod()

        self.assertFalse(f.has_axes())
        self.assertIsNone(f.get_axes(None))
        self.assertIsNone(f.set_axes(["time"]))
        self.assertTrue(f.has_axes())
        self.assertEqual(f.get_axes(), ("time",))
        self.assertEqual(f.del_axes(), ("time",))
        self.assertIsNone(f.del_axes(None))

    def test_CellMethod_method(self):
        """Test the method access and (un)setting CellMethod methods."""
        f = cfdm.CellMethod()

        self.assertFalse(f.has_method())
        self.assertIsNone(f.get_method(None))
        self.assertIsNone(f.set_method("mean"))
        self.assertTrue(f.has_method())
        self.assertEqual(f.get_method(), "mean")
        self.assertEqual(f.del_method(), "mean")
        self.assertIsNone(f.del_method(None))

    def test_CellMethod_qualifier(self):
        """Test qualifier access and (un)setting CellMethod methods."""
        f = cfdm.CellMethod()

        self.assertEqual(f.qualifiers(), {})
        self.assertFalse(f.has_qualifier("within"))
        self.assertIsNone(f.get_qualifier("within", None))
        self.assertIsNone(f.set_qualifier("within", "years"))
        self.assertEqual(f.qualifiers(), {"within": "years"})
        self.assertTrue(f.has_qualifier("within"))
        self.assertEqual(f.get_qualifier("within"), "years")
        self.assertEqual(f.del_qualifier("within"), "years")
        self.assertIsNone(f.del_qualifier("within", None))
        self.assertEqual(f.qualifiers(), {})


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
