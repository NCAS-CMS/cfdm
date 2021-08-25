import datetime
import faulthandler
import os
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class CellMeasureTest(unittest.TestCase):
    """Unit test for the CellMeasure class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, f"f={f!r}")
        self.f = f[0]

    def test_CellMeasure__init__(self):
        """Test the CellMeasure constructor and source keyword."""
        cfdm.CellMeasure(source="qwerty")

    def test_CellMeasure__repr__str__dump_construct_type(self):
        """Test all means of CellMeasure inspection."""
        f = self.f

        for cm in f.cell_measures().values():
            _ = repr(cm)
            _ = str(cm)
            self.assertIsInstance(cm.dump(display=False), str)
            self.assertEqual(cm.construct_type, "cell_measure")

    def test_CellMeasure(self):
        """Test measure access and (un)setting CellMeasure methods."""
        f = self.f.copy()

        cm = f.construct("measure:area")

        self.assertTrue(cm.has_measure())
        self.assertTrue(cm.get_measure(), "area")

        measure = cm.del_measure()
        self.assertFalse(cm.has_measure())
        self.assertIsNone(cm.get_measure(None))
        self.assertIsNone(cm.del_measure(None))

        cm.set_measure(measure)
        self.assertTrue(cm.has_measure())
        self.assertEqual(cm.get_measure(), "area")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
