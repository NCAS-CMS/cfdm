import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class RaggedIndexedContiguousArrayTest(unittest.TestCase):
    """Unit test for the RaggedIndexedContiguousArray class."""

    r = cfdm.RaggedIndexedContiguousArray(
        compressed_array=cfdm.Data(
            [
                280.0,
                281.0,
                279.0,
                278.0,
                279.5,
                281.0,
                282.0,
                278.0,
                279.0,
                277.5,
            ]
        ),
        shape=(2, 2, 3),
        index_variable=cfdm.Index(data=[0, 0, 0, 0, 1, 1, 1, 1]),
        count_variable=cfdm.Count(data=[1, 3, 2, 2]),
    )

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

    def test_RaggedIndexedContiguousArray_to_memory(self):
        """Test `RaggedIndexedContiguousArray.to_memory`"""
        self.assertIsInstance(
            self.r.to_memory(), cfdm.RaggedIndexedContiguousArray
        )

    def test_RaggedIndexedContiguousArray_get_count(self):
        """Test `RaggedIndexedContiguousArray.get_count`"""
        r = self.r.copy()
        self.assertIsInstance(r.get_count(), cfdm.Count)
        r._del_component("count_variable")
        self.assertIsNone(r.get_count(None))

    def test_RaggedIndexedContiguousArray_get_index(self):
        """Test `RaggedIndexedContiguousArray.get_index`"""
        r = self.r.copy()
        self.assertIsInstance(r.get_index(), cfdm.Index)
        r._del_component("index_variable")
        self.assertIsNone(r.get_index(None))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
