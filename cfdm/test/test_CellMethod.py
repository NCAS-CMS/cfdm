from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm


class CellMethodTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []


    def test_CellMethod__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for c in f.cell_methods.values():
            _ = repr(c)
            _ = str(c)
            _ = c.dump(display=False)
            self.assertTrue(c.construct_type == 'cell_method')


    def test_CellMethod(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        # ------------------------------------------------------------
        # Equals and idenities
        # ------------------------------------------------------------
        for c in f.cell_methods.values():
            d = c.copy()
            self.assertTrue(c.equals(c, verbose=3))
            self.assertTrue(c.equals(d, verbose=3))
            self.assertTrue(d.equals(c, verbose=3))
            self.assertTrue(c.identity() == 'method:'+c.get_method())
            self.assertTrue(c.identities() == ['method:'+c.get_method()])

        # ------------------------------------------------------------
        # Sorted
        # ------------------------------------------------------------
        c = cfdm.CellMethod(method='minimum',
                            axes=['B', 'A'],
                            qualifiers={'interval': [1, 2]})

        d = cfdm.CellMethod(method='minimum',
                            axes=['A', 'B'],
                            qualifiers={'interval': [2, 1]})

        self.assertTrue(d.equals(c.sorted(), verbose=3))

        c = cfdm.CellMethod(method='minimum',
                            axes=['B', 'A'],
                            qualifiers={'interval': [3]})

        d = cfdm.CellMethod(method='minimum',
                            axes=['A', 'B'],
                            qualifiers={'interval': [3]})

        self.assertTrue(d.equals(c.sorted(), verbose=3))

        c = cfdm.CellMethod(method='minimum',
                            axes=['area'],
                            qualifiers={'interval': [3]})

        d = cfdm.CellMethod(method='minimum',
                            axes=['area'],
                            qualifiers={'interval': [3]})

        self.assertTrue(d.equals(c.sorted(), verbose=3))


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
