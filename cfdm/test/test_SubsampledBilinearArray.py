import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class SubsampledBilinearArrayTest(unittest.TestCase):
    """Unit test for the SubsampledBilinearArray class."""

    tie_point_indices = {
        0: cfdm.TiePointIndex(data=[0, 8, 9, 17]),
        1: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11]),
    }

    c = cfdm.SubsampledBilinearArray(
        compressed_array=cfdm.Data(
            np.array(
                [
                    [0, 4, 7, 8, 11],
                    [96, 100, 103, 104, 107],
                    [108, 112, 115, 116, 119],
                    [204, 208, 211, 212, 215],
                ]
            )
        ),
        shape=(18, 12),
        ndim=2,
        size=18 * 12,
        compressed_axes=[0, 1],
        tie_point_indices=tie_point_indices,
        computational_precision="64",
    )

    # bounds tie points
    b = cfdm.SubsampledBilinearArray(
        compressed_array=cfdm.Data(
            np.array(
                [
                    [0, 5, 8, 8, 12],
                    [117, 122, 125, 125, 129],
                    [117, 122, 125, 125, 129],
                    [234, 239, 242, 242, 246],
                ]
            )
        ),
        shape=(18, 12, 4),
        ndim=3,
        size=18 * 12 * 4,
        compressed_axes=[0, 1],
        tie_point_indices=tie_point_indices,
        computational_precision="64",
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

    def test_SubsampledBilinearArray__getitem__(self):
        """TODO"""
        a = np.arange(18 * 12).reshape(18, 12)
        d = cfdm.Data(self.c)[...]
        self.assertEqual(d.shape, a.shape)
        self.assertTrue(np.allclose(d, a))

        # bounds tie points
        a = np.arange(19 * 13).reshape(19, 13)
        a = np.transpose(
            np.stack([a[:-1, :-1], a[:-1, 1:], a[1:, 1:], a[1:, :-1:]]),
            [1, 2, 0],
        )
        d = cfdm.Data(self.b)[...]
        self.assertEqual(d.shape, a.shape)
        self.assertTrue(np.allclose(d, a))
        
    def test_SubsampledBilinearArray_dtype(self):
        """TODO"""
        d = self.c
        self.assertEqual(d.dtype, d._default_dtype)
        d.dtype = np.dtype('float32')
        self.assertEqual(d.dtype, np.dtype('float32'))

if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
