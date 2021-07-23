import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class RaggedIndexedContiguousArrayTest(unittest.TestCase):
    """Unit test for the RaggedIndexedContiguousArray class."""

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
        """Test the `to_memory` RaggedIndexedContiguousArray method."""
        compressed_data = cfdm.Data(
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
        )

        index = cfdm.Index(data=[0, 0, 0, 0, 1, 1, 1, 1])

        cfdm.Count(data=[1, 3, 2, 2])

        r = cfdm.RaggedIndexedContiguousArray(
            compressed_data,
            shape=(2, 2, 3),
            size=12,
            ndim=3,
            index_variable=index,
            count_variable=index,
        )

        r.to_memory()


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
