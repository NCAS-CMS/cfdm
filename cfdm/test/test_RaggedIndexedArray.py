import datetime
import unittest

import cfdm


class RaggedIndexedArrayTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_RaggedIndexedArray_to_memory(self):
        compressed_data = cfdm.Data([280.0, 281.0, 279.0, 278.0, 279.5])

        index = cfdm.Index(data=[0, 1, 1, 1])

        r = cfdm.RaggedIndexedArray(compressed_data, shape=(2, 3),
                                    size=6, ndim=2,
                                    index_variable=index)

        r.to_memory()

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
