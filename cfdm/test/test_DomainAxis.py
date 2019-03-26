from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class DomainTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_DomainAxis__repr__str_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for d in f.domain_axes.values():            
            _ = repr(d)
            _ = str(d)
            self.assertTrue(d.construct_type == 'domain_axis')
    #--- End: def

    def test_DomainAxis_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        d = list(f.domain_axes.values())[0]
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=True))
        self.assertTrue(d.equals(e, verbose=True))
        self.assertTrue(e.equals(d, verbose=True))
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
