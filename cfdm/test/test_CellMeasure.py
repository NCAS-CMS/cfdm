from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class CellMeasureTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_CellMeasure__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for cm in f.cell_measures.values():
            _ = repr(cm)
            _ = str(cm)
            _ = cm.dump(display=False)
            self.assertTrue(cm.construct_type == 'cell_measure')
    #--- End: def

    def test_CellMeasure(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        cm = f.construct('measure:area')

        self.assertTrue(cm.has_measure())
        self.assertTrue(cm.get_measure() == 'area')
        _ = cm.del_measure()
        self.assertFalse(cm.has_measure())
        self.assertTrue(cm.get_measure(None) == None)
        self.assertTrue(cm.del_measure(None) == None)
        cm.set_measure(_)
        self.assertTrue(cm.has_measure())
        self.assertTrue(cm.get_measure() == 'area')
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
