import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class SubsampledLinearArrayTest(unittest.TestCase):
    """Unit test for the SubsampledLinearArray class."""

    tie_point_indices = {0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])}

    c = cfdm.SubsampledLinearArray(
        compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
        shape=(12,),
        ndim=1,
        size=12,
        compressed_axes=[0],
        tie_point_indices=tie_point_indices,
    )

    # bounds tie points
    b = cfdm.SubsampledLinearArray(
        compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
        shape=(12, 2),
        ndim=2,
        size=24,
        compressed_axes=[0],
        tie_point_indices=tie_point_indices,
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

    def test_SubsampledLinearArray__getitem__(self):
        """TODO"""
        a = np.linspace(15, 345, 12)
        d = cfdm.Data(self.c)
        self.assertTrue(np.allclose(d[...], np.linspace(15, 345, 12)))

        # bounds tie points
        a = np.transpose(
            np.stack([np.linspace(0, 330, 12), np.linspace(30, 360, 12)])
        )
        d = cfdm.Data(self.b)

        self.assertTrue(np.allclose(d[...], a))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
