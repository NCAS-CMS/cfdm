import datetime
import copy
import numpy
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class NumpyArrayTest(unittest.TestCase):
    """TODO DOCS."""

    def setUp(self):
        """TODO DOCS."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows: cfdm.LOG_LEVEL('DEBUG')
        #
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_NumpyArray_copy(self):
        """TODO DOCS."""
        a = numpy.array([1, 2, 3, 4])

        x = cfdm.NumpyArray(a)
        y = copy.deepcopy(x)
        self.assertTrue((x.array == a).all())
        self.assertTrue((x.array == y.array).all())

    def test_NumpyArray__array__(self):
        """TODO DOCS."""
        a = numpy.array([1, 2, 3, 4])

        x = cfdm.NumpyArray(a)

        b = numpy.array(x)
        self.assertTrue((b == a).all())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
