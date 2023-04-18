import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class SubsampledArrayTest(unittest.TestCase):
    """Unit test for the SubsampledArray class."""

    tie_point_indices = cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])

    w = cfdm.InterpolationParameter(data=[5, 10, 5])

    coords = cfdm.SubsampledArray(
        interpolation_name="quadratic",
        compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
        shape=(12,),
        tie_point_indices={0: tie_point_indices},
        parameters={"w": w},
        parameter_dimensions={"w": (0,)},
    )

    u_coords = np.array(
        [
            15.0,
            48.75,
            80.0,
            108.75,
            135.0,
            173.88888889,
            203.88888889,
            225.0,
            255.0,
            289.44444444,
            319.44444444,
            345.0,
        ]
    )

    bounds = cfdm.SubsampledArray(
        interpolation_name="quadratic",
        compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
        shape=(12, 2),
        tie_point_indices={0: tie_point_indices},
        parameters={"w": w},
        parameter_dimensions={"w": (0,)},
    )
    u_bounds = np.array(
        [
            [0.0, 33.2],
            [33.2, 64.8],
            [64.8, 94.80000000000001],
            [94.80000000000001, 123.2],
            [123.2, 150.0],
            [150.0, 188.88888888888889],
            [188.88888888888889, 218.88888888888889],
            [218.88888888888889, 240.0],
            [240.0, 273.75],
            [273.75, 305.0],
            [305.0, 333.75],
            [333.75, 360.0],
        ]
    )

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_SubsampledArray__getitem__(self):
        """Test `SubsampledArray.__getitem__`"""
        coords = self.coords[...]
        bounds = self.bounds[...]
        self.assertEqual(coords.shape, self.u_coords.shape)
        self.assertEqual(bounds.shape, self.u_bounds.shape)
        self.assertTrue(np.allclose(coords, self.u_coords))
        self.assertTrue(np.allclose(bounds, self.u_bounds))

    def test_SubsampledArray_to_memory(self):
        """Test `SubsampledArray.to_memory."""
        self.assertIsInstance(self.coords.to_memory(), cfdm.SubsampledArray)

    def test_SubsampledArray_compressed_dimensions(self):
        """Test `SubsampledArray.compressed_dimensions."""
        self.assertEqual(self.coords.compressed_dimensions(), {0: (0,)})

        c = cfdm.SubsampledArray()
        with self.assertRaises(ValueError):
            c.compressed_dimensions()


#    def test_SubsampledArray_get_filename(self):
#        """Test SubsampledArray.get_filename."""
#        x = self.coords
#        self.assertIsNone(x.get_filename(None))
#
#        with self.assertRaises(AttributeError):
#            x.get_filename()
#
#    def test_SubsampledArray_get_filenames(self):
#        """Test `SubsampledArray.get_filenames."""
#        self.assertEqual(self.coords.get_filenames(), set())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
