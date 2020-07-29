import datetime
import inspect
import os
import unittest

import numpy

import cfdm


class CellMeasureTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []

    def test_CellMeasure__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for cm in f.cell_measures.values():
            _ = repr(cm)
            _ = str(cm)
            self.assertIsInstance(cm.dump(display=False), str)
            self.assertEqual(cm.construct_type, 'cell_measure')

    def test_CellMeasure(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        cm = f.construct('measure:area')

        self.assertTrue(cm.has_measure())
        self.assertTrue(cm.get_measure(), 'area')

        measure = cm.del_measure()
        self.assertFalse(cm.has_measure())
        self.assertIsNone(cm.get_measure(None))
        self.assertIsNone(cm.del_measure(None))

        cm.set_measure(measure)
        self.assertTrue(cm.has_measure())
        self.assertEqual(cm.get_measure(), 'area')

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
