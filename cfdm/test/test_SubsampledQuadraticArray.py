import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class SubsampledQuadraticArrayTest(unittest.TestCase):
    """Unit test for the SubsampledQuadraticArray class."""

    tie_point_indices = {0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])}

    parameters = {"w": cfdm.InterpolationParameter(data=[5, 10, 5])}

    c = cfdm.SubsampledQuadraticArray(
        compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
        shape=(12,),
        ndim=1,
        size=12,
        tie_point_indices=tie_point_indices,
        interpolation_parameters=parameters,
        parameter_dimensions={"w": (0,)},
        computational_precision="64",
    )

    # bounds tie points
    b = cfdm.SubsampledQuadraticArray(
        compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
        shape=(12, 2),
        ndim=2,
        size=24,
        tie_point_indices=tie_point_indices,
        interpolation_parameters=parameters,
        parameter_dimensions={"w": (0,)},
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

    def test_SubsampledQuadraticArray__getitem__(self):
        """TODO."""
        a = np.array(
            [
                15,
                48.75,
                80,
                108.75,
                135,
                173.88888889,
                203.88888889,
                225,
                255,
                289.44444444,
                319.44444444,
                345,
            ]
        )
        d = cfdm.Data(self.c)[...]
        self.assertEqual(d.shape, a.shape)
        self.assertTrue(np.allclose(d, a))

        # bounds tie points
        a = np.array(
            [
                [0, 33.2],
                [33.2, 64.8],
                [64.8, 94.8],
                [94.8, 123.2],
                [123.2, 150],
                [150, 188.88888889],
                [188.88888889, 218.88888889],
                [218.88888889, 240],
                [240, 273.75],
                [273.75, 305.0],
                [305.0, 333.75],
                [333.75, 360],
            ]
        )
        d = cfdm.Data(self.b)[...]
        self.assertEqual(d.shape, a.shape)
        self.assertTrue(np.allclose(d, a))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
