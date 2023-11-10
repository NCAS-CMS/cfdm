import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

# Create testcell connectivity object
c = cfdm.CellConnectivity()
c.set_properties({"long_name": "neighbour faces for faces"})
c.nc_set_variable("Mesh2_face_links")
data = cfdm.Data(
    [
        [0, 1, 2, -99, -99],
        [1, 0, -99, -99, -99],
        [2, 0, -99, -99, -99],
    ],
    dtype="i4",
)
data.masked_values(-99, inplace=True)
c.set_data(data)
c.set_connectivity("edge")


class CellConnectivityTest(unittest.TestCase):
    """Unit test for the CellConnectivity class."""

    c = c

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_CellConnectivity__repr__str__dump(self):
        """Test all means of CellConnectivity inspection."""
        c = self.c
        self.assertEqual(
            repr(c), "<CellConnectivity: connectivity:edge(3, 5) >"
        )
        self.assertEqual(str(c), "connectivity:edge(3, 5) ")
        self.assertEqual(
            c.dump(display=False),
            """Cell Connectivity: connectivity:edge
    long_name = 'neighbour faces for faces'
    Data(3, 5) = [[0, ..., --]]""",
        )

    def test_CellConnectivity_copy(self):
        """Test the copy of CellConnectivity."""
        c = self.c
        self.assertTrue(c.equals(c.copy()))

    def test_CellConnectivity_data(self):
        """Test the data of CellConnectivity."""
        c = self.c
        self.assertEqual(c.ndim, 1)

    def test_CellConnectivity_connectivity(self):
        """Test the 'connectivity' methods of CellConnectivity."""
        c = self.c.copy()
        self.assertTrue(c.has_connectivity())
        self.assertEqual(c.get_connectivity(), "edge")
        self.assertEqual(c.del_connectivity(), "edge")
        self.assertFalse(c.has_connectivity())
        self.assertIsNone(c.get_connectivity(None))
        self.assertIsNone(c.del_connectivity(None))

        with self.assertRaises(ValueError):
            c.get_connectivity()

        with self.assertRaises(ValueError):
            c.del_connectivity()

        self.assertIsNone(c.set_connectivity("edge"))
        self.assertTrue(c.has_connectivity())
        self.assertEqual(c.get_connectivity(), "edge")

    def test_CellConnectivity_transpose(self):
        """Test the 'transpose' method of CellConnectivity."""
        c = self.c.copy()
        d = c.transpose()
        self.assertTrue(c.equals(d))
        self.assertIsNone(c.transpose(inplace=True))

        for axes in ([1], [1, 0], [3]):
            with self.assertRaises(ValueError):
                c.transpose(axes)

    def test_CellConnectivity_normalise(self):
        """Test the 'normalise' method of CellConnectivity."""
        data = cfdm.Data(
            [[4, 1, 10, 125], [1, 4, -99, -99], [125, 4, -99, -99]],
            mask_value=-99,
        )
        d = cfdm.CellConnectivity(connectivity="edge", data=data)

        n = np.ma.array([[0, 1, 2, -99], [1, 0, -99, -99], [2, 0, -99, -99]])
        n = np.ma.where(n == -99, np.ma.masked, n)

        d0 = d.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())
        d1 = d.normalise(start_index=1).array
        self.assertEqual(d1.shape, n.shape)
        self.assertTrue((d1.mask == n.mask).all())
        self.assertTrue((d1 == n + 1).all())

        e = d.copy()
        self.assertIsNone(e.normalise(inplace=True))
        d0 = e.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())
        d1 = e.normalise(start_index=1).array
        self.assertEqual(d1.shape, n.shape)
        self.assertTrue((d1.mask == n.mask).all())
        self.assertTrue((d1 == n + 1).all())

        self.assertIsNone(e.normalise(start_index=1, inplace=True))
        d0 = e.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())
        d1 = e.normalise(start_index=1).array
        self.assertEqual(d1.shape, n.shape)
        self.assertTrue((d1.mask == n.mask).all())
        self.assertTrue((d1 == n + 1).all())

        d.data[:, -1] = np.ma.masked
        n = np.ma.array([[0, 1, -99, -99], [1, 0, -99, -99], [2, 0, -99, -99]])
        n = np.ma.where(n == -99, np.ma.masked, n)

        d0 = d.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())

        d.data[:, 1:] = np.ma.masked
        n = np.ma.array(
            [[0, -99, -99, -99], [1, -99, -99, -99], [2, -99, -99, -99]]
        )
        n = np.ma.where(n == -99, np.ma.masked, n)
        d0 = d.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())

        n = np.ma.array([[0], [1], [2]])
        d0 = d.normalise(remove_empty_columns=True).array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
