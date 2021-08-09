import copy
import datetime
import faulthandler
import itertools
import unittest
from unittest.mock import patch

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

# Note: it is important we test on the cfdm logging config rather than the
# generic Python module logging (i.e. 'cfdm.logging' not just 'logging').
# Also, mimic the use in the codebase by using a module-specific logger:
log_name = __name__
logger = cfdm.logging.getLogger(log_name)


DEBUG_MSG = "A major clue to solving the evasive bug"
DETAIL_MSG = "In practice this will be very detailed."
INFO_MSG = "This should be short and sweet"
WARNING_MSG = "Best pay attention to this!"


@cfdm.decorators._manage_log_level_via_verbosity
def decorated_logging_func(verbose=None):
    """Dummy function to log messages at various levels by decorator.

    See also dummyClass.decorated_logging_method which does the same but
    as a method rather than a function.

    """
    logger.debug(DEBUG_MSG)
    logger.detail(DETAIL_MSG)
    logger.info(INFO_MSG)
    logger.warning(WARNING_MSG)


class dummyClass:
    """Dummy class acting as container to test methods.

    This is a special class to test appropriate methods as proper
    instance methods, mirroring their context in the codebase.

    """

    def __init__(self):
        """Constructor for dummyClass."""
        self._list = [1]

        self.debug_message = DEBUG_MSG
        self.detail_message = DETAIL_MSG
        self.info_message = INFO_MSG
        self.warning_message = WARNING_MSG

        self.dummy_string = "foo bar baz"

    def copy(self):
        """Creates a deep copy."""
        return copy.deepcopy(self)  # note a shallow copy is not sufficient

    def func(self, inplace):
        """Dummy function to do something trivial to a mutable object.

        The operation is potentially done in-place as specified by an
        in-place flag.

        """
        if inplace:
            d = self
        else:
            d = self.copy()

        d._list.append(2)

        if inplace:
            d = None
        return d

    @cfdm.decorators._inplace_enabled(False)
    def decorated_func(self, inplace):
        """Dummy function that is 'func' except managed by decorator.

        The decorator manages whether or not the operation is applied
        in-place.

        """
        d = cfdm.decorators._inplace_enabled_define_and_cleanup(self)
        d._list.append(2)
        return d

    def print_or_return_string(self, display=True):
        """Dummy function to either print or return a given string.

        It prints the string if the display argument is True, else it
        returns it.

        """
        string = self.dummy_string

        if display:
            print(string)
        else:
            return string

    @cfdm.decorators._display_or_return
    def print_or_return_string_by_decorator(self, display=True):
        """Equivalent to 'print_or_return_string' but via decorator.

        The decorator manages whether or not to print rather than return
        depending on whether or not the display argument is True.

        """
        return self.dummy_string

    @cfdm.decorators._manage_log_level_via_verbosity
    def decorated_logging_method(self, verbose=None):
        """Method to log messages at various levels by decorator.

        See also decorated_logging_func which does the same but as a
        function rather than a method.

        """
        logger.debug(self.debug_message)
        logger.detail(self.detail_message)
        logger.info(self.info_message)
        logger.warning(self.warning_message)


class decoratorsTest(unittest.TestCase):
    """Test the decorators module."""

    def test_inplace_enabled(self):
        """Test the `_inplace_enabled` decorator."""
        # Note we must initiate separate classes as a list is mutable:
        test_class_1 = dummyClass()
        test_class_2 = dummyClass()

        # Test when not in-place
        res_1 = test_class_1.func(inplace=False)
        res_2 = test_class_2.decorated_func(inplace=False)
        self.assertEqual(test_class_1._list, test_class_2._list)
        self.assertEqual(test_class_2._list, [1])  # as original list untouched
        self.assertEqual(res_1._list, res_2._list)
        self.assertEqual(res_2._list, [1, 2])  # as return d copy, not original

        # Test when in-place
        res_3 = test_class_1.func(inplace=True)
        res_4 = test_class_2.decorated_func(inplace=True)

        self.assertEqual(test_class_1._list, test_class_2._list)
        # As do the operation in-place on the original (class) list object:
        self.assertEqual(test_class_2._list, [1, 2])
        self.assertEqual(res_3, res_4)
        self.assertEqual(res_4, None)  # as return None if inplace=True

    def test_manage_log_level_via_verbosity(self):
        """Test the `_manage_log_level_via_verbosity` decorator."""
        # Order of decreasing severity/verbosity is crucial to one test below
        levels = ["WARNING", "INFO", "DETAIL", "DEBUG"]

        # Note we test assertions on the root logger object, which is the
        # one output overall at runtime, but the specific module logger name
        # should be registered within the log message:
        log_message = [
            f"WARNING:{log_name}:{WARNING_MSG}",
            f"INFO:{log_name}:{INFO_MSG}",
            f"DETAIL:{log_name}:{DETAIL_MSG}",
            f"DEBUG:{log_name}:{DEBUG_MSG}",
        ]

        test_class = dummyClass()
        # 1. First test it works for methods using test_class to test with
        # 2. Then test it works for functions (not bound to a class)
        functions_to_call_to_test = [
            test_class.decorated_logging_method,  # Case 1 as described above
            decorated_logging_func,  # Case 2
        ]

        for level, function_to_call_to_test in itertools.product(
            levels, functions_to_call_to_test
        ):
            cfdm.log_level(level)  # reset to level

            # Default verbose(=None) cases: log_level should determine output
            with self.assertLogs(level=cfdm.log_level().value) as catch:
                function_to_call_to_test()

                for msg in log_message:
                    # log_level should prevent messages less severe appearing:
                    if levels.index(level) >= log_message.index(msg):
                        self.assertIn(msg, catch.output)
                    else:  # less severe, should be effectively filtered out
                        self.assertNotIn(msg, catch.output)

            # Cases where verbose is set; value should override log_level...

            # Highest verbosity case (note -1 == 'DEBUG', highest verbosity):
            # all messages should appear, regardless of global log_level:
            for argument in (-1, "DEBUG", "debug", "Debug", "DeBuG"):
                with self.assertLogs(level=cfdm.log_level().value) as catch:
                    function_to_call_to_test(verbose=argument)
                    for msg in log_message:
                        self.assertIn(msg, catch.output)

            # Lowest verbosity case ('WARNING' / 1) excluding special case of
            # 'DISABLE' (see note above): only warning messages should appear,
            # regardless of global log_level value set:
            for argument in (1, "WARNING", "warning", "Warning", "WaRning"):
                with self.assertLogs(level=cfdm.log_level().value) as catch:
                    function_to_call_to_test(verbose=argument)
                    for msg in log_message:
                        if msg.split(":")[0] == "WARNING":
                            self.assertIn(msg, catch.output)
                        else:
                            self.assertNotIn(msg, catch.output)

            # Boolean cases for testing backwards compatibility...

            # ... verbose=True should be equivalent to verbose=3 now:
            with self.assertLogs(level=cfdm.log_level().value) as catch:
                function_to_call_to_test(verbose=True)
                for msg in log_message:
                    if msg.split(":")[0] == "DEBUG":
                        self.assertNotIn(msg, catch.output)
                    else:
                        self.assertIn(msg, catch.output)

            # ... verbose=False should be equivalent to verbose=0 now, so
            # test along with 'DISABLE' special case below...

            # Special 'DISABLE' (0) case: note this needs to be last as we
            # reset the log_level to it but need to use 'NOTSET' for the
            # assertLogs level, which sends all log messages through:
            for argument in (0, "DISABLE", "disable", "Disable", "DisAblE"):
                with self.assertLogs(level="NOTSET") as catch:
                    # Note: get 'AssertionError' if don't log anything at all,
                    # so to avoid this and allow check for disabled logging,
                    # first log something then disable and check that no other
                    # messages emerge:
                    logger.info(
                        "Purely to keep 'assertLog' happy: see comment!"
                    )
                    cfdm.log_level("DISABLE")
                    function_to_call_to_test(verbose=argument)
                    for msg in log_message:  # nothing else should be logged
                        self.assertNotIn(msg, catch.output)

            # verbose=False should be equivalent in behaviour to verbose=0
            with self.assertLogs(level="NOTSET") as catch:
                logger.info("Purely to keep 'assertLog' happy: see previous!")
                function_to_call_to_test(verbose=False)
                for msg in log_message:  # nothing else should be logged
                    self.assertNotIn(msg, catch.output)

    @patch("builtins.print")
    def test_display_or_return(self, mock_print):
        """Test the `_display_or_return` decorator."""
        test_class = dummyClass()

        # Compare results with display=False:
        res_1 = test_class.print_or_return_string(display=False)
        res_2 = test_class.print_or_return_string_by_decorator(display=False)
        self.assertEqual(res_1, res_2)
        mock_print.assert_not_called()  # checks nothing was printed to STDOUT

        # Compare results with display=True:
        res_3 = test_class.print_or_return_string_by_decorator(display=True)
        mock_print.assert_called_with(test_class.dummy_string)
        # Should print rather than return, so returns None by default:
        self.assertEqual(res_3, None)

        new_string = "Let's change it up"
        test_class.dummy_string = new_string
        # Compare defaults, where default should be display=True i.e. to print
        res_4 = test_class.print_or_return_string_by_decorator()
        mock_print.assert_called_with(new_string)
        self.assertEqual(res_4, None)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
