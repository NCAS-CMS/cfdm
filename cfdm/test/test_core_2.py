import copy
import datetime
import unittest

import numpy

import cfdm


class Core2Test(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_core_NumpyArray(self):
        a = cfdm.core.NumpyArray(numpy.array([1, 2, 3]))

        # __deepcopy__
        b = copy.deepcopy(a)

        # __array__
        b = numpy.array(a)
        b = numpy.array(a, dtype='float')

    def test_core_Container(self):
        # __init__
        a = cfdm.core.Container(source='qwerty')

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
