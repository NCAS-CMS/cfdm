from __future__ import print_function
import datetime
import inspect
import unittest

import cfdm


class FunctionsTest(unittest.TestCase):
    def setUp(self):
        # Disable non-critical log messages to silence expected warnings/errors
        cfdm.LOG_SEVERITY_LEVEL('CRITICAL')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.LOG_SEVERITY_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_SEVERITY_LEVEL('CRITICAL')

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
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
