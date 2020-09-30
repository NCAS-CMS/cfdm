import datetime
import unittest

import cfdm


class CFDMImplementationTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')
        self.i = cfdm.implementation()

    def test_CFDMImplementation__init__(self):
        i = cfdm.CFDMImplementation({'NewClass1': 'qwerty',
                                     'NewClass2': None})

    def test_CFDMImplementation_classes(self):
        self.assertIsInstance(self.i.classes(), dict)

    def test_CFDMImplementation_set_class(self):
        self.i.set_class('NewClass', 'qwerty')

    def test_CFDMImplementation_get_class(self):
        self.assertIs(self.i.get_class('Field'), cfdm.Field)

        with self.assertRaises(ValueError):
            self.i.get_class('qwerty')

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
