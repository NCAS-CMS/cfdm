import datetime
import faulthandler
import unittest

import numpy as np
from scipy.sparse import coo_array

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

row = np.array([0, 3, 1, 0])
col = np.array([0, 3, 1, 2])
data = np.array([4, 5, 7, 9])
s = coo_array((data, (row, col)), shape=(4, 4))


class SparseArrayTest(unittest.TestCase):
    """Unit test for the SparseArray class."""

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

    def test_SparseArray_copy(self):
        """Test the copy module copying behaviour of SparseArray."""
        x = cfdm.SparseArray(s)
        self.assertTrue((s.toarray() == x.array).all())

    def test_SparseArray__array__(self):
        """Test the numpy array conversion of SparseArray."""
        x = cfdm.SparseArray(s)
        self.assertTrue((np.array(x) == x.array).all())

    def test_SparseArray_get_filename(self):
        """Test SparseArray.get_filename."""
        x = cfdm.SparseArray()
        with self.assertRaises(AttributeError):
            x.get_filename()

    def test_SparseArray_get_filenames(self):
        """Test SparseArray.get_filenames."""
        x = cfdm.SparseArray()
        with self.assertRaises(AttributeError):
            x.get_filenames()


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
