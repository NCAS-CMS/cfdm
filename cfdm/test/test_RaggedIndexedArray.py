import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class RaggedIndexedArrayTest(unittest.TestCase):
    """Unit test for the RaggedIndexedArray class."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        compressed_data = cfdm.Data([280.0, 281.0, 279.0, 278.0, 279.5])
        index = cfdm.Index(data=[0, 1, 1, 1])
        self.r = cfdm.RaggedIndexedArray(
            compressed_data, shape=(2, 3), size=6, ndim=2, index_variable=index
        )

    def test_RaggedIndexedArray_to_memory(self):
        """Test the `to_memory` RaggedIndexedArray method."""
        self.assertIsInstance(self.r.to_memory(), cfdm.RaggedIndexedArray)

    def test_RaggedIndexedArray_get_index(self):
        """Test the `get_index` RaggedIndexedArray method."""
        r = self.r
        self.assertIsInstance(r.get_index(), cfdm.Index)
        r._del_component("index_variable")
        self.assertIsNone(r.get_index(None))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
