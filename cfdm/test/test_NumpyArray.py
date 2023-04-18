import copy
import datetime
import faulthandler
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class NumpyArrayTest(unittest.TestCase):
    """Unit test for the NumpyArray class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
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
        """Test the copy module copying behaviour of NumpyArray."""
        a = numpy.array([1, 2, 3, 4])

        x = cfdm.NumpyArray(a)
        y = copy.deepcopy(x)
        self.assertTrue((x.array == a).all())
        self.assertTrue((x.array == y.array).all())

    def test_NumpyArray__array__(self):
        """Test the NumPy array conversion of NumpyArray."""
        a = numpy.array([1, 2, 3, 4])

        x = cfdm.NumpyArray(a)

        b = numpy.array(x)
        self.assertTrue((b == a).all())

    def test_NumpyArray_get_filename(self):
        """Test NumpyArray.get_filename."""
        x = cfdm.NumpyArray()
        with self.assertRaises(AttributeError):
            x.get_filename()

    def test_NumpyArray_get_filenames(self):
        """Test NumpyArray.get_filenames."""
        x = cfdm.NumpyArray()
        with self.assertRaises(AttributeError):
            x.get_filenames()


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
