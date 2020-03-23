from __future__ import print_function
import datetime
import inspect
import unittest

import cfdm


class FunctionsTest(unittest.TestCase):
    def setUp(self):
        self.test_only = []
        
    def test_ATOL_RTOL(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        org = cfdm.RTOL()
        self.assertTrue(cfdm.RTOL(1e-5) == org)
        self.assertTrue(cfdm.RTOL() == 1e-5)
        self.assertTrue(cfdm.RTOL(org) == 1e-5)
        self.assertTrue(cfdm.RTOL() == org)
        
        org = cfdm.ATOL()
        self.assertTrue(cfdm.ATOL(1e-5) == org)
        self.assertTrue(cfdm.ATOL() == 1e-5)
        self.assertTrue(cfdm.ATOL(org) == 1e-5)
        self.assertTrue(cfdm.ATOL() == org)

    def test_CF(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertTrue(cfdm.CF() == cfdm.core.__cf_version__)

    def test_environment(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        _ = cfdm.environment(display=False)
        _ = cfdm.environment(display=False, paths=False)
        _ = cfdm.environment(display=False)

    def test_example_field(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for n in range(7):
            f = cfdm.example_field(n)
            _ = f.data.array
            _ = f.dump(display=False)

        with self.assertRaises(Exception):
            _ = cfdm.example_field(-999)

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
