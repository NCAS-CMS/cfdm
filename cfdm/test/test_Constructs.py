from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class ConstructsTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_Constructs__repr__str__dump(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        c = f.constructs
        _ = repr(c)
        _ = str(c)
    #--- End: def

    def test_Constructs_key_items_value(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        for key, value in f.constructs.items():
            x = f.constructs.filter_by_key(key)
            self.assertTrue(x.key() == key)
            self.assertTrue(x.value().equals(value))
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment())
    print('')
    unittest.main(verbosity=2)
