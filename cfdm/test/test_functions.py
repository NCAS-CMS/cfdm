import atexit
import copy
import datetime
import faulthandler
import logging
import os
import platform
import sys
import tempfile
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_functions.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(temp_file,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class FunctionsTest(unittest.TestCase):
    """Test the functions of the non-core functions module."""

    @classmethod
    def setUpClass(cls):
        """Preparations called before the test class runs."""
        # Need to run this per-class, not per-method, to access the
        # original value of log_level to use to test the default (see
        # test_log_level)
        cls.original = cfdm.log_level("DISABLE")

        # When this module is run as part of full test-suite, the
        # value set in previous test is picked up above, not the
        # default. For now skip this test (effectively) for test suite
        # run. TODO: find way round this.
        if __name__ != "__main__":
            cls.original = "WARNING"

        # (no tearDownClass necessary)

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warning, but
        # save original state for test on logging (see test_log_level)
        cfdm.log_level("DISABLE")
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
        valid_log_values = [-1, "INFO", 3, 2, 1, "DEBUG", "DETAIL", "WARNING"]
        # 'DISABLE' (0) is special case so exclude from levels list:
        self.valid_level_values = copy.copy(valid_log_values)
        # Cover string names, numeric code equivalents, & case
        # sensitivity:
        self.valid_log_values_ci = valid_log_values[:-2] + [
            "Detail",
            0,
            "DISABLE",
            "warning",
        ]

    def test_atol_rtol(self):
        """Test the atol and rtol functions."""
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
        """Test the `log_level` function."""
        original = self.__class__.original  # original to module i.e. default

        self.assertEqual(original, "WARNING")  # test default
        cfdm.LOG_LEVEL(original)  # reset from setUp() value to avoid coupling

        # Now test getting and setting for all valid values in turn,
        # where use fact that setting returns old value hence set
        # value on next call:
        previous = cfdm.log_level()
        for value in self.valid_log_values_ci:
            self.assertEqual(cfdm.LOG_LEVEL(value), previous)
            previous = cfdm.LOG_LEVEL()  # update previous value

            # Some conversions to equivalent, standardised return value:
            if isinstance(value, int) and cfdm._is_valid_log_level_int(
                value
            ):  # str from LOG_LEVEL
                value = cfdm.constants.ValidLogLevels(value).name  # convert
            if isinstance(value, str):  # LOG_LEVEL returns all caps string
                value = value.upper()
            self.assertEqual(previous, value)

        with self.assertRaises(ValueError):
            cfdm.log_level(4)
            cfdm.LOG_LEVEL(4)  # check alias too
        with self.assertRaises(ValueError):
            cfdm.log_level("ERROR")  # notable as is valid Python logging level
            cfdm.LOG_LEVEL("ERROR")

    def test_reset_log_emergence_level(self):
        """Test the `_reset_log_emergence_level` internal function."""
        # 'DISABLE' is special case so test it afterwards (see below)
        for value in self.valid_level_values:
            cfdm.functions._reset_log_emergence_level(value)

            # getLevelName() converts to string. Otherwise gives
            # Python logging int equivalent, which is not the scale we use:
            if isinstance(value, int) and cfdm._is_valid_log_level_int(value):
                value = cfdm.constants.ValidLogLevels(value).name

            self.assertTrue(
                cfdm.logging.getLevelName(cfdm.logging.getLogger().level)
                == value
            )
        # Now test 'DISABLE' (0) special case; should not change level as such
        previous = logging.getLevelName(cfdm.logging.getLogger().level)
        cfdm.functions._reset_log_emergence_level("DISABLE")
        self.assertTrue(
            cfdm.logging.getLevelName(cfdm.logging.getLogger().level)
            == previous
        )
        # ... but test that it has disabled logging, as it is designed to do!
        self.assertFalse(cfdm.logging.getLogger().isEnabledFor(logging.DEBUG))
        self.assertFalse(
            cfdm.logging.getLogger().isEnabledFor(logging.WARNING)
        )

    def test_disable_logging(self):
        """Test the `_disable_logging` internal function."""
        # Re-set to avoid coupling; use set level to check it is
        # restored after
        cfdm.log_level("DETAIL")
        below_detail_values = [logging.DEBUG]
        at_or_above_detail_values = [
            cfdm.logging._nameToLevel["DETAIL"],
            logging.INFO,
            logging.WARNING,
        ]

        # Does it disable logging correctly?
        cfdm.functions._disable_logging()

        for value in below_detail_values + at_or_above_detail_values:
            self.assertFalse(cfdm.logging.getLogger().isEnabledFor(value))

        # And does it re-enable after having disabled logging if use
        # 'NOTSET'?
        cfdm.functions._disable_logging("NOTSET")  # should re-enable

        # Re-enabling should revert emergence in line with log
        # severity level:
        for value in at_or_above_detail_values:  # as long as level >= 'DETAIL'
            self.assertTrue(cfdm.logging.getLogger().isEnabledFor(value))
        # 'DEBUG' is effectively not "enabled" as is less severe than
        # 'DETAIL'
        self.assertFalse(cfdm.logging.getLogger().isEnabledFor(logging.DEBUG))

    def test_CF(self):
        """Test the CF function."""
        self.assertEqual(cfdm.CF(), cfdm.core.__cf_version__)

    def test_environment(self):
        """Test the `environment` function."""
        e = cfdm.environment(display=False)
        ep = cfdm.environment(display=False, paths=False)

        self.assertIsInstance(e, list)
        self.assertIsInstance(ep, list)

        components = ["Platform: ", "netCDF4: ", "numpy: ", "cftime: "]
        for component in components:
            self.assertTrue(any(s.startswith(component) for s in e))
            self.assertTrue(any(s.startswith(component) for s in ep))
        for component in [
            f"cfdm: {cfdm.__version__} {os.path.abspath(cfdm.__file__)}",
            f"Python: {platform.python_version()} {sys.executable}",
        ]:
            self.assertIn(component, e)
            self.assertNotIn(component, ep)  # paths shouldn't be present here
        for component in [
            f"cfdm: {cfdm.__version__}",
            f"Python: {platform.python_version()}",
        ]:
            self.assertIn(component, ep)

    def test_example_field(self):
        """Test the `example_field` function."""
        top = 8

        example_fields = cfdm.example_fields()
        self.assertEqual(len(example_fields), top)

        for f in example_fields:
            _ = f.data.array

            self.assertIsInstance(f.dump(display=False), str)

            cfdm.write(f, temp_file)
            g = cfdm.read(temp_file, verbose=1)

            self.assertEqual(len(g), 1)
            self.assertTrue(f.equals(g[0], verbose=3))

        with self.assertRaises(Exception):
            cfdm.example_field(top + 1)

        with self.assertRaises(ValueError):
            cfdm.example_field(1, 2)

        with self.assertRaises(TypeError):
            cfdm.example_field(1, 2, 3)

        self.assertEqual(len(cfdm.example_fields(0)), 1)
        self.assertEqual(len(cfdm.example_fields(0, 2)), 2)
        self.assertEqual(len(cfdm.example_fields(0, 2, 0)), 3)

    def test_abspath(self):
        """Test the abspath function."""
        filename = "test_file.nc"
        self.assertEqual(cfdm.abspath(filename), os.path.abspath(filename))
        filename = "http://test_file.nc"
        self.assertEqual(cfdm.abspath(filename), filename)
        filename = "https://test_file.nc"
        self.assertEqual(cfdm.abspath(filename), filename)

    def test_configuration(self):
        """Test the configuration function."""
        # Test getting of all config. and store original values to test on:
        org = cfdm.configuration()
        self.assertIsInstance(org, dict)
        self.assertEqual(len(org), 3)
        org_atol = org["atol"]
        self.assertIsInstance(org_atol, float)
        org_rtol = org["rtol"]
        self.assertIsInstance(org_rtol, float)
        org_ll = org["log_level"]  # will be 'DISABLE' as disable for test
        self.assertIsInstance(org_ll, str)

        # Store some sensible values to reset items to for testing,
        # ensure these are kept to be different to the defaults:
        atol_rtol_reset_value = 7e-10
        ll_reset_value = "DETAIL"

        # Test the setting of each lone item:
        cfdm.configuration(atol=atol_rtol_reset_value)
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], atol_rtol_reset_value)
        self.assertEqual(post_set["rtol"], org_rtol)
        self.assertEqual(post_set["log_level"], org_ll)
        cfdm.configuration(atol=org_atol)  # reset to org

        cfdm.configuration(rtol=atol_rtol_reset_value)
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], org_atol)
        self.assertEqual(post_set["rtol"], atol_rtol_reset_value)
        self.assertEqual(post_set["log_level"], org_ll)
        # don't reset to org this time to test change persisting...

        # Note setting of previous items persist, e.g. atol above
        cfdm.configuration(log_level=ll_reset_value)
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], org_atol)
        self.assertEqual(
            post_set["rtol"], atol_rtol_reset_value
        )  # since changed it above
        self.assertEqual(post_set["log_level"], ll_reset_value)

        # Test the setting of more than one, but not all, items simultaneously:
        new_atol_rtol_reset_value = 5e-18
        new_ll_reset_value = "DEBUG"
        cfdm.configuration(
            rtol=new_atol_rtol_reset_value, log_level=new_ll_reset_value
        )
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], org_atol)
        self.assertEqual(post_set["rtol"], new_atol_rtol_reset_value)
        self.assertEqual(post_set["log_level"], new_ll_reset_value)

        # Test setting all possible items simultaneously (to originals):
        cfdm.configuration(
            atol=org_atol,  # same as current setting, testing on 'no change'
            rtol=org_rtol,
            log_level=org_ll,
        )
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], org_atol)
        self.assertEqual(post_set["rtol"], org_rtol)
        self.assertEqual(post_set["log_level"], org_ll)

        # Test edge cases & invalid inputs...
        # ... 1. User might set '0' or 'True' in some cases, which is
        # somewhat a risk area for error as 0 is Falsy & True a Bool:
        cfdm.configuration(rtol=0, atol=0.0, log_level=0)
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], 0.0)
        self.assertEqual(post_set["rtol"], 0.0)
        self.assertEqual(post_set["log_level"], "DISABLE")  # DISABLE == 0
        cfdm.configuration(log_level=True)  # deprecated but valid value
        # Deprecated True is converted to value 'WARNING' by log_level
        self.assertEqual(cfdm.configuration()["log_level"], "WARNING")

        # 2. None as an input kwarg rather than as a default:
        cfdm.configuration(atol=None, log_level=None, rtol=org_rtol)
        post_set = cfdm.configuration()
        self.assertEqual(post_set["atol"], 0.0)  # 0.0 as set above
        self.assertEqual(post_set["rtol"], org_rtol)
        self.assertEqual(post_set["log_level"], "WARNING")  # as set above

        # 3. Gracefully error with useful error messages with invalid inputs:
        with self.assertRaises(ValueError):
            cfdm.configuration(rtol="bad")
        with self.assertRaises(ValueError):
            cfdm.configuration(log_level=7)

        # 4. Check invalid kwarg given logic processes **kwargs:
        with self.assertRaises(TypeError):
            cfdm.configuration(bad_kwarg=1e-15)

        old = cfdm.configuration()
        try:
            cfdm.configuration(atol=888, rtol=999, log_level="BAD")
        except ValueError:
            self.assertEqual(cfdm.configuration(), old)
        else:
            raise RuntimeError(
                "A ValueError should have been raised, but wasn't"
            )

    def test_unique_constructs(self):
        """TODO DOCS."""
        f = cfdm.example_field(0)
        g = cfdm.example_field(1)

        self.assertFalse(cfdm.unique_constructs([]))

        self.assertEqual(len(cfdm.unique_constructs([f])), 1)
        self.assertEqual(len(cfdm.unique_constructs([f, f])), 1)
        self.assertEqual(len(cfdm.unique_constructs([f, f.copy()])), 1)
        self.assertEqual(len(cfdm.unique_constructs([f, f.copy(), g])), 2)

        fields = [f, f, g]
        domains = [x.domain for x in (f, f, g)]

        self.assertEqual(len(cfdm.unique_constructs(domains)), 2)
        self.assertEqual(len(cfdm.unique_constructs(domains + fields)), 4)
        self.assertEqual(
            len(cfdm.unique_constructs(domains + fields + [f.domain])), 4
        )

        # Test generator
        domains = (x.domain for x in ())
        self.assertEqual(len(cfdm.unique_constructs(domains)), 0)

        domains = (x.domain for x in (f,))
        self.assertEqual(len(cfdm.unique_constructs(domains)), 1)

        domains = (x.domain for x in (f, f, g))
        self.assertEqual(len(cfdm.unique_constructs(domains)), 2)

    def test_context_managers(self):
        """Test the context manager support of the functions."""
        # rtol and atol
        for func in (
            cfdm.atol,
            cfdm.rtol,
        ):
            old = func()
            new = old * 2
            with func(new):
                self.assertEqual(func(), new)
                self.assertEqual(func(new * 2), new)
                self.assertEqual(func(), new * 2)

            self.assertEqual(func(), old)

        # log_level
        func = cfdm.log_level

        org = func("DETAIL")
        old = func()
        new = "DEBUG"
        with func(new):
            self.assertEqual(func(), new)

        self.assertEqual(func(), old)
        func(org)

        del org._func
        with self.assertRaises(AttributeError):
            with org:
                pass

        # Full configuration
        func = cfdm.configuration

        org = func(rtol=10, atol=20, log_level="DETAIL")
        old = func()
        new = dict(rtol=10 * 2, atol=20 * 2, log_level="DEBUG")
        with func(**new):
            self.assertEqual(func(), new)

        self.assertEqual(func(), old)
        func(**org)

        org = func(rtol=cfdm.Constant(10), atol=20, log_level="DETAIL")
        old = func()
        new = dict(rtol=cfdm.Constant(10 * 2), atol=20 * 2, log_level="DEBUG")
        with func(**new):
            self.assertEqual(func(), new)

        self.assertEqual(func(), old)
        func(**org)

    def test_Constant(self):
        """Test the Constant class."""
        c = cfdm.Constant(20)
        d = cfdm.Constant(10)
        e = cfdm.Constant(999)

        self.assertIsInstance(hash(c), int)
        self.assertIsInstance(repr(c), str)

        self.assertEqual(float(c), 20.0)
        self.assertEqual(int(c), 20)
        self.assertEqual(str(c), "20")

        # Binary operations
        self.assertEqual(c, 20)
        self.assertEqual(20, c)
        self.assertEqual(c, c)
        self.assertEqual(c, copy.deepcopy(c))
        self.assertEqual(c, numpy.array(20))

        self.assertNotEqual(c, 999)
        self.assertNotEqual(999, c)
        self.assertNotEqual(c, d)
        self.assertNotEqual(c, numpy.array(999))
        self.assertNotEqual(numpy.array(999), c)

        self.assertLess(c, 999)
        self.assertLessEqual(c, 999)
        self.assertGreater(c, 10)
        self.assertGreaterEqual(c, 10)

        self.assertGreater(999, c)
        self.assertGreaterEqual(999, c)
        self.assertLess(10, c)
        self.assertLessEqual(10, c)

        self.assertLess(c, e)
        self.assertLessEqual(c, e)
        self.assertGreater(c, d)
        self.assertGreaterEqual(c, d)

        self.assertEqual(c + 10, 30)
        self.assertEqual(c - 10, 10)
        self.assertEqual(c / 10, 2)
        self.assertEqual(c * 10, 200)
        self.assertEqual(c // 10, 2)

        self.assertEqual(c + d, 30)
        self.assertEqual(c - d, 10)
        self.assertEqual(c / d, 2)
        self.assertEqual(c * d, 200)
        self.assertEqual(c // d, 2)

        self.assertEqual(20 + d, 30)
        self.assertEqual(20 - d, 10)
        self.assertEqual(20 / d, 2)
        self.assertEqual(20 * d, 200)
        self.assertEqual(20 // d, 2)

        c = cfdm.Constant(20)
        c -= 10
        self.assertEqual(c, 10)
        c += 10
        self.assertEqual(c, 20)
        c *= 10
        self.assertEqual(c, 200)
        c /= 10
        self.assertEqual(c, 20)
        c //= 10
        self.assertEqual(c, 2)

        # Unary operations
        c = cfdm.Constant(-20)
        self.assertEqual(-c, 20)
        self.assertEqual(abs(c), 20)
        self.assertEqual(+c, -20)

        # Copy
        c = cfdm.atol().copy()
        del c._func
        self.assertEqual(c, c.copy())

        # Bool
        self.assertTrue(cfdm.Constant(1))
        self.assertTrue(cfdm.Constant(True))
        self.assertFalse(cfdm.Constant(0))
        self.assertFalse(cfdm.Constant(False))

    def test_Configuration(self):
        """Test the Configuration class."""
        c = cfdm.configuration()

        self.assertIsInstance(repr(c), str)
        self.assertEqual(str(c), str(dict(**c)))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
