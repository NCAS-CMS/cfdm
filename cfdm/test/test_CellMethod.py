from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class CellMethodTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_CellMethod__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for cm in f.cell_methods.values():
            print (repr(cm))
            _ = repr(cm)
            _ = str(cm)
            _ = cm.dump(display=False)
            self.assertTrue(cm.construct_type == 'cell_method')
    #--- End: def

    def test_CellMethod(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        for cm in f.cell_methods.values():
            self.assertTrue(cm.equals(cm, verbose=True))
            self.assertTrue(cm.equals(cm.copy(), verbose=True))
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
