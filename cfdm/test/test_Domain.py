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


    def test_Domain__repr__str__dump(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = self.f.domain

        _ = repr(d)
        _ = str(d)
        _ = d.dump(display=False)


    def test_Domain_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        d = f.domain
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=True))
        self.assertTrue(d.equals(e, verbose=True))
        self.assertTrue(e.equals(d, verbose=True))


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
