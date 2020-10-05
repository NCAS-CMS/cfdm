import datetime
import unittest

import cfdm


class RaggedContiguousArrayTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        compressed_data = cfdm.Data([280.0, 281.0, 279.0, 278.0, 279.5])
        count = cfdm.Count(data=[1, 3])
        self.r = cfdm.RaggedContiguousArray(compressed_data, shape=(2, 3),
                                            size=6, ndim=2,
                                            count_variable=count)

    def test_RaggedContiguousArray_to_memory(self):
        self.assertIsInstance(self.r.to_memory(), cfdm.RaggedContiguousArray)

    def test_RaggedContiguousArray_get_count(self):
        r = self.r
        self.assertIsInstance(r.get_count(), cfdm.Count)
        r._del_component('count_variable')
        self.assertIsNone(r.get_count(None))

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
