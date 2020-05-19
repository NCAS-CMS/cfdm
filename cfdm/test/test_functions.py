from __future__ import print_function
import copy
import datetime
import inspect
import logging
import unittest

import cfdm


class FunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Need to run this per-class, not per-method, to access the original
        # value of LOG_LEVEL to use to test the default (see test_LOG_LEVEL)
        cls.original = cfdm.LOG_LEVEL('DISABLE')

        # When this module is run as part of full test-suite, the value set in
        # previous test is picked up above, not the default. For now skip this
        # test (effectively) for test suite run. TODO: find way round this.
        if __name__ != '__main__':
            cls.original = 'WARNING'

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

        # Cover all below except lower-case, not supported in some functions:
        valid_log_values = [
            -1, 'INFO', 3, 2, 1, 'DEBUG', 'DETAIL', 'WARNING']
        # 'DISABLE' (0) is special case so exclude from levels list:
        self.valid_level_values = copy.copy(valid_log_values)
        # Cover string names, numeric code equivalents, & case sensitivity:
        self.valid_log_values_ci = valid_log_values[:-2] + [
            'Detail', 0, 'DISABLE', 'warning']

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
        cfdm.LOG_LEVEL(original)  # reset from setUp() value to avoid coupling

        # Now test getting and setting for all valid values in turn, where use
        # fact that setting returns old value hence set value on next call:
        previous = cfdm.LOG_LEVEL()
        for value in self.valid_log_values_ci:
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

    def test_reset_log_emergence_level(self):
        # 'DISABLE' is special case so test it afterwards (see below)
        for value in self.valid_level_values:
            cfdm.functions._reset_log_emergence_level(value)

            # getLevelName() converts to string. Otherwise gives Python
            # logging int equivalent, which is not the scale we use.
            if isinstance(value, int):
                value = cfdm.constants.numeric_log_level_map[value]

            self.assertTrue(
                cfdm.logging.getLevelName(cfdm.logging.getLogger().level) ==
                value
            )
        # Now test 'DISABLE' (0) special case; should not change level as such
        previous = logging.getLevelName(cfdm.logging.getLogger().level)
        cfdm.functions._reset_log_emergence_level('DISABLE')
        self.assertTrue(
            cfdm.logging.getLevelName(cfdm.logging.getLogger().level) ==
            previous
        )
        # ... but test that it has disabled logging, as it is designed to do!
        self.assertFalse(cfdm.logging.getLogger().isEnabledFor(logging.DEBUG))
        self.assertFalse(
            cfdm.logging.getLogger().isEnabledFor(logging.WARNING))

    def test_disable_logging(self):
        # Re-set to avoid coupling; use set level to check it is restored after
        original = cfdm.LOG_LEVEL('DETAIL')
        below_detail_values = [logging.DEBUG]
        at_or_above_detail_values = [
            cfdm.logging._nameToLevel['DETAIL'], logging.INFO, logging.WARNING
        ]

        # Does it disable logging correctly?
        cfdm.functions._disable_logging()

        for value in below_detail_values + at_or_above_detail_values:
            self.assertFalse(cfdm.logging.getLogger().isEnabledFor(value))

        # And does it re-enable after having disabled logging if use 'NOTSET'?
        cfdm.functions._disable_logging('NOTSET')  # should re-enable

        # Re-enabling should revert emergence in line with log severity level:
        for value in at_or_above_detail_values:  # as long as level >= 'DETAIL'
            self.assertTrue(cfdm.logging.getLogger().isEnabledFor(value))
        # 'DEBUG' is effectively not "enabled" as is less severe than 'DETAIL'
        self.assertFalse(cfdm.logging.getLogger().isEnabledFor(logging.DEBUG))

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

        top = 7

        for n in range(top + 1):
            f = cfdm.example_field(n)
            _ = f.data.array
            _ = f.dump(display=False)

        with self.assertRaises(Exception):
            _ = cfdm.example_field(top + 1)

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
