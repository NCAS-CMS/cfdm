import copy
import datetime
import unittest

import cfdm

import logging

# Note: it is important we test on the cfdm logging config rather than the
# generic Python module logging (i.e. 'cfdm.logging' not just 'logging').
# Also, mimic the use in the codebase by using a module-specific logger:
log_name = __name__
logger = cfdm.logging.getLogger(log_name)


class dummyClass:
    '''Dummy class acting as container to test methods as proper instance
       methods, mirroring their context in the codebase.
    '''
    def __init__(self):
        self._list = [1]

        self.debug_message = "A major clue to solving the evasive bug"
        self.detail_message = "In practice this will be very detailed."
        self.info_message = "This should be short and sweet"
        self.warning_message = "Best pay attention to this!"

    def copy(self):
        return copy.deepcopy(self)  # note a shallow copy is not sufficient

    def func(self, inplace):
        '''Dummy function to do something trivial to a mutable object,
           potentially in-place as toggled by an in-place flag.
        '''
        if inplace:
            d = self
        else:
            d = self.copy()

        d._list.append(2)

        if inplace:
            d = None
        return d

    @cfdm.decorators._inplace_enabled
    def decorated_func(self, inplace):
        '''Dummy function equivalent to 'func' but a decorator manages the
           logic to specify and conduct in-place operation.
        '''
        d = cfdm.decorators._inplace_enabled_define_and_cleanup(self)
        d._list.append(2)
        return d

    @cfdm.decorators._manage_log_level_via_verbosity
    def decorated_logging_func(self, verbose=None):
        logger.debug(self.debug_message)
        logger.detail(self.detail_message)
        logger.info(self.info_message)
        logger.warning(self.warning_message)

# --- End: class


class DecoratorsTest(unittest.TestCase):
    def setUp(self):
        self.test_only = []

    def test_inplace_enabled(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

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
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        test_class = dummyClass()

        # Order of decreasing severity/verbosity is crucial to one test below
        levels = ['WARNING', 'INFO', 'DETAIL', 'DEBUG']

        # Note we test assertions on the root logger object, which is the
        # one output overall at runtime, but the specific module logger name
        # should be registered within the log message:
        log_message = [
            'WARNING:{}:{}'.format(log_name, test_class.warning_message),
            'INFO:{}:{}'.format(log_name, test_class.info_message),
            'DETAIL:{}:{}'.format(log_name, test_class.detail_message),
            'DEBUG:{}:{}'.format(log_name, test_class.debug_message)
        ]

        for level in levels:
            cfdm.LOG_LEVEL(level)  # reset to level

            # Default verbose(=None) cases: LOG_LEVEL should determine output
            with self.assertLogs(level=cfdm.LOG_LEVEL()) as catch:
                test_class.decorated_logging_func()

                for msg in log_message:
                    # LOG_LEVEL should prevent messages less severe appearing:
                    if levels.index(level) >= log_message.index(msg):
                        self.assertIn(msg, catch.output)
                    else:  # less severe, should be effectively filtered out
                        self.assertNotIn(msg, catch.output)

            # Cases where verbose is set; value should override LOG_LEVEL...

            # Highest verbosity case (note -1 == 'DEBUG', highest verbosity):
            # all messages should appear, regardless of global LOG_LEVEL:
            with self.assertLogs(level=cfdm.LOG_LEVEL()) as catch:
                test_class.decorated_logging_func(verbose=-1)
                for msg in log_message:
                    self.assertIn(msg, catch.output)

            # Lowest verbosity case ('WARNING' / 1) excluding special case of
            # 'DISABLE' (see note above): only warning messages should appear,
            # regardless of global LOG_LEVEL value set:
            with self.assertLogs(level=cfdm.LOG_LEVEL()) as catch:
                test_class.decorated_logging_func(verbose=1)
                for msg in log_message:
                    if msg.split(":")[0] == 'WARNING':
                        self.assertIn(msg, catch.output)
                    else:
                        self.assertNotIn(msg, catch.output)

            # Boolean cases for testing backwards compatibility...

            # ... verbose=True should be equivalent to verbose=3 now:
            with self.assertLogs(level=cfdm.LOG_LEVEL()) as catch:
                test_class.decorated_logging_func(verbose=True)
                for msg in log_message:
                    if msg.split(":")[0] == 'DEBUG':
                        self.assertNotIn(msg, catch.output)
                    else:
                        self.assertIn(msg, catch.output)

            # ... verbose=False should be equivalent to verbose=0 now, so
            # test along with 'DISABLE' special case below...

            # Special 'DISABLE' (0) case: note this needs to be last as we
            # reset the LOG_LEVEL to it but need to use 'NOTSET' for the
            # assertLogs level, which sends all log messages through:
            with self.assertLogs(level='NOTSET') as catch:
                # Note get 'AssertionError' if don't log anything at all, so
                # avoid this and allow check for disabled logging, first log
                # something then disable and check nothing else emerges:
                logger.info("Purely to keep 'assertLog' happy: see comment!")
                cfdm.LOG_LEVEL('DISABLE')
                test_class.decorated_logging_func(verbose=0)
                for msg in log_message:  # nothing else should be logged
                    self.assertNotIn(msg, catch.output)

            # verbose=False should be equivalent in behaviour to verbose=0
            with self.assertLogs(level='NOTSET') as catch:
                logger.info("Purely to keep 'assertLog' happy: see previous!")
                test_class.decorated_logging_func(verbose=False)
                for msg in log_message:  # nothing else should be logged
                    self.assertNotIn(msg, catch.output)


# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
