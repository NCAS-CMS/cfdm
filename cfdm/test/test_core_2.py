import copy
import datetime
import unittest

import numpy as np

import cfdm


class Core2Test(unittest.TestCase):
    """Unit test for the `cfdm.core` package."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_core_NumpyArray(self):
        """Test cfdm.core.NumpyArray class."""
        a = cfdm.core.NumpyArray(np.array([1, 2, 3]))

        # __deepcopy__
        copy.deepcopy(a)

        # __array__
        np.array(a)
        np.array(a, dtype="float")

    def test_core_Container(self):
        """Test cfdm.core.Container class."""
        cfdm.core.Container(source="qwerty")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
