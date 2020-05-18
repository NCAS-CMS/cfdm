from __future__ import print_function
import datetime
import inspect
import unittest

import cfdm


class FunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Need to run this per-class, not per-method, to access the original
        # value of LOG_LEVEL to use to test the default (see test_LOG_LEVEL)
        cls.original = cfdm.LOG_LEVEL('DISABLE')
        # (no tearDownClass necessary)

    def setUp(self):
        # Disable log messages to silence expected warning, but
        # save original state for test on logging (see test_LOG_LEVEL)
        cfdm.LOG_LEVEL('DISABLE')
        # Note that test_LOG_LEVEL has been designed so the the above call will
        # not influence it, so it may be adjusted without changing that test

        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

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

    def test_LOG_LEVEL(self):
        original = self.__class__.original  # original to module i.e. default
        self.assertTrue(original == 'WARNING')  # test default

        # Now test getting and setting for all valid values in turn, where use
        # fact that setting returns old value hence set value on next call:
        cfdm.LOG_LEVEL(original)  # reset from setUp() value to avoid coupling
        previous = cfdm.LOG_LEVEL()
        # Cover string names, numeric code equivalents, & case sensitivity
        test_valid_values = [
            'INFO', -1, 'DISABLE', 1, 'DEBUG', 2, 'Detail', 'warning', 0, 3]
        for value in test_valid_values:
            self.assertTrue(cfdm.LOG_LEVEL(value) == previous)
            previous = cfdm.LOG_LEVEL()  # update previous value

            # Some conversions to equivalent, standardised return value:
            if isinstance(value, int):  # LOG_LEVEL returns the string not int
                value = cfdm.constants.numeric_log_level_map[value]
            if isinstance(value, str):  # LOG_LEVEL returns all caps string
                value = value.upper()
            self.assertTrue(previous == value)

        with self.assertRaises(ValueError):
            cfdm.LOG_LEVEL(4)
        with self.assertRaises(ValueError):
            cfdm.LOG_LEVEL('ERROR')  # notable as is valid Python logging level

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
