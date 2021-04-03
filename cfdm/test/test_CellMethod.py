import datetime
import os
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class CellMethodTest(unittest.TestCase):
    """TODO DOCS."""

    def setUp(self):
        """TODO DOCS."""
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
        self.assertEqual(len(f), 1, "f={!r}".format(f))
        self.f = f[0]

    def test_CellMethod__repr__str__dump_construct_type(self):
        """TODO DOCS."""
        f = self.f

        for c in f.cell_methods().values():
            _ = repr(c)
            _ = str(c)
            self.assertIsInstance(c.dump(display=False), str)
            self.assertEqual(c.construct_type, "cell_method")

    def test_CellMethod(self):
        """TODO DOCS."""
        f = self.f

        # ------------------------------------------------------------
        # Equals and idenities
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
        """TODO DOCS."""
        f = cfdm.CellMethod()

        self.assertFalse(f.has_axes())
        self.assertIsNone(f.get_axes(None))
        self.assertIsNone(f.set_axes(["time"]))
        self.assertTrue(f.has_axes())
        self.assertEqual(f.get_axes(), ("time",))
        self.assertEqual(f.del_axes(), ("time",))
        self.assertIsNone(f.del_axes(None))

    def test_CellMethod_method(self):
        """TODO DOCS."""
        f = cfdm.CellMethod()

        self.assertFalse(f.has_method())
        self.assertIsNone(f.get_method(None))
        self.assertIsNone(f.set_method("mean"))
        self.assertTrue(f.has_method())
        self.assertEqual(f.get_method(), "mean")
        self.assertEqual(f.del_method(), "mean")
        self.assertIsNone(f.del_method(None))

    def test_CellMethod_qualifier(self):
        """TODO DOCS."""
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
