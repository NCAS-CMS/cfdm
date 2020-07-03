import atexit
import copy
import datetime
import inspect
import logging
import os
import tempfile
import unittest

import cfdm


n_tmpfiles = 1
tmpfiles = [tempfile.mktemp('_test_groups.nc', dir=os.getcwd())
            for i in range(n_tmpfiles)]
(temp_file,
) = tmpfiles

def _remove_tmpfiles():
    '''Remove temporary files created during tests.

    '''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass

atexit.register(_remove_tmpfiles)


class FunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Need to run this per-class, not per-method, to access the
        # original value of log_level to use to test the default (see
        # test_log_level)
        cls.original = cfdm.log_level('DISABLE')

        # When this module is run as part of full test-suite, the
        # value set in previous test is picked up above, not the
        # default. For now skip this test (effectively) for test suite
        # run. TODO: find way round this.
        if __name__ != '__main__':
            cls.original = 'WARNING'

        # (no tearDownClass necessary)

    def setUp(self):
        # Disable log messages to silence expected warning, but
        # save original state for test on logging (see test_log_level)
        cfdm.log_level('DISABLE')
        # Note that test_log_level has been designed so the the above
        # call will not influence it, so it may be adjusted without
        # changing that test

        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:        
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        # Cover all below except lower-case, not supported in some
        # functions:
        valid_log_values = [
            -1, 'INFO', 3, 2, 1, 'DEBUG', 'DETAIL', 'WARNING']
        # 'DISABLE' (0) is special case so exclude from levels list:
        self.valid_level_values = copy.copy(valid_log_values)
        # Cover string names, numeric code equivalents, & case
        # sensitivity:
        self.valid_log_values_ci = valid_log_values[:-2] + [
            'Detail', 0, 'DISABLE', 'warning']

        self.test_only = []

    def test_atol_rtol(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        org = cfdm.RTOL()
        self.assertEqual(cfdm.RTOL(1e-5), org)
        self.assertEqual(cfdm.RTOL(), 1e-5)
        self.assertEqual(cfdm.RTOL(org), 1e-5)
        self.assertEqual(cfdm.RTOL(), org)

        org = cfdm.ATOL()
        self.assertEqual(cfdm.ATOL(1e-5), org)
        self.assertEqual(cfdm.ATOL(), 1e-5)
        self.assertEqual(cfdm.ATOL(org), 1e-5)
        self.assertEqual(cfdm.ATOL(), org)

        org = cfdm.atol()
        self.assertTrue(org == cfdm.ATOL())  # check alias

        self.assertTrue(cfdm.atol(1e-5) == org)
        self.assertTrue(cfdm.atol() == 1e-5)
        self.assertTrue(cfdm.atol(org) == 1e-5)
        self.assertTrue(cfdm.atol() == org)

    def test_log_level(self):
        original = self.__class__.original  # original to module i.e. default

        self.assertEqual(original, 'WARNING')  # test default
        cfdm.LOG_LEVEL(original)  # reset from setUp() value to avoid coupling

        # Now test getting and setting for all valid values in turn,
        # where use fact that setting returns old value hence set
        # value on next call:
        previous = cfdm.log_level()
        for value in self.valid_log_values_ci:
            self.assertEqual(cfdm.LOG_LEVEL(value), previous)
            previous = cfdm.LOG_LEVEL()  # update previous value

            # Some conversions to equivalent, standardised return
            # value:
            if isinstance(value, int):  # LOG_LEVEL returns the string not int
                value = cfdm.constants.numeric_log_level_map[value]
            if isinstance(value, str):  # LOG_LEVEL returns all caps string
                value = value.upper()
            self.assertEqual(previous, value)

        with self.assertRaises(ValueError):
            cfdm.log_level(4)
            cfdm.LOG_LEVEL(4)  # check alias too
        with self.assertRaises(ValueError):
            cfdm.log_level('ERROR')  # notable as is valid Python logging level
            cfdm.LOG_LEVEL('ERROR')

    def test_reset_log_emergence_level(self):
        # 'DISABLE' is special case so test it afterwards (see below)
        for value in self.valid_level_values:
            cfdm.functions._reset_log_emergence_level(value)

            # getLevelName() converts to string. Otherwise gives
            # Python logging int equivalent, which is not the scale we use:
            if (isinstance(value, int) and
                cfdm._is_valid_log_level_int(value)):
                value = cfdm.constants.ValidLogLevels(value).name

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
        # Re-set to avoid coupling; use set level to check it is
        # restored after
        original = cfdm.log_level('DETAIL')
        below_detail_values = [logging.DEBUG]
        at_or_above_detail_values = [
            cfdm.logging._nameToLevel['DETAIL'], logging.INFO, logging.WARNING
        ]

        # Does it disable logging correctly?
        cfdm.functions._disable_logging()

        for value in below_detail_values + at_or_above_detail_values:
            self.assertFalse(cfdm.logging.getLogger().isEnabledFor(value))

        # And does it re-enable after having disabled logging if use
        # 'NOTSET'?
        cfdm.functions._disable_logging('NOTSET')  # should re-enable

        # Re-enabling should revert emergence in line with log
        # severity level:
        for value in at_or_above_detail_values:  # as long as level >= 'DETAIL'
            self.assertTrue(cfdm.logging.getLogger().isEnabledFor(value))
        # 'DEBUG' is effectively not "enabled" as is less severe than
        # 'DETAIL'
        self.assertFalse(cfdm.logging.getLogger().isEnabledFor(logging.DEBUG))

    def test_CF(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertEqual(cfdm.CF(), cfdm.core.__cf_version__)

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

            cfdm.write(f, temp_file)
            g = cfdm.read(temp_file)

            self.assertEqual(len(g), 1)
            self.assertTrue(f.equals(g[0], verbose=3), 'n={}'.format(n))
            
        with self.assertRaises(Exception):
            _ = cfdm.example_field(top + 1)

    def test_abspath(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        filename = 'test_file.nc'
        self.assertEqual(cfdm.abspath(filename), os.path.abspath(filename))
        filename = 'http://test_file.nc'
        self.assertEqual(cfdm.abspath(filename), filename)
        filename = 'https://test_file.nc'
        self.assertEqual(cfdm.abspath(filename), filename)

#    def test_default_netCDF_fill_values(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#        
#        self.assertIsInstance(cfdm.default_netCDF_fill_values(), dict)

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
