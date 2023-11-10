import datetime
import faulthandler
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

# Create test domain topology object
c = cfdm.DomainTopology()
c.set_properties({"long_name": "Maps every face to its corner nodes"})
c.nc_set_variable("Mesh2_face_nodes")
data = cfdm.Data(
    [[2, 3, 1, 0], [6, 7, 3, 2], [1, 3, 8, -99]],
    dtype="i4",
)
data.masked_values(-99, inplace=True)
c.set_data(data)
c.set_cell("face")


class DomainTopologyTest(unittest.TestCase):
    """Unit test for the DomainTopology class."""

    d = c

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

    def test_DomainTopology__repr__str__dump(self):
        """Test all means of DomainTopology inspection."""
        d = self.d
        self.assertEqual(repr(d), "<DomainTopology: cell:face(3, 4) >")
        self.assertEqual(str(d), "cell:face(3, 4) ")
        self.assertEqual(
            d.dump(display=False),
            """Domain Topology: cell:face
    long_name = 'Maps every face to its corner nodes'
    Data(3, 4) = [[2, ..., --]]""",
        )

    def test_DomainTopology_copy(self):
        """Test the copy of DomainTopology."""
        d = self.d
        self.assertTrue(d.equals(d.copy()))

    def test_DomainTopology_data(self):
        """Test the data of DomainTopology."""
        d = self.d
        self.assertEqual(d.ndim, 1)

    def test_DomainTopology_cell(self):
        """Test the 'cell' methods of DomainTopology."""
        d = self.d.copy()
        self.assertTrue(d.has_cell())
        self.assertEqual(d.get_cell(), "face")
        self.assertEqual(d.del_cell(), "face")
        self.assertFalse(d.has_cell())
        self.assertIsNone(d.get_cell(None))
        self.assertIsNone(d.del_cell(None))

        with self.assertRaises(ValueError):
            d.get_cell()

        with self.assertRaises(ValueError):
            d.set_cell("bad value")

        self.assertIsNone(d.set_cell("face"))
        self.assertTrue(d.has_cell())
        self.assertEqual(d.get_cell(), "face")

    def test_DomainTopology_transpose(self):
        """Test the 'transpose' method of DomainTopology."""
        d = self.d.copy()
        e = d.transpose()
        self.assertTrue(d.equals(e))
        self.assertIsNone(d.transpose(inplace=True))

        for axes in ([1], [1, 0], [3]):
            with self.assertRaises(ValueError):
                d.transpose(axes)

    def test_DomainTopology_normalise(self):
        """Test the 'normalise' method of DomainTopology."""
        # Face cells
        data = cfdm.Data(
            [[1, 4, 5, 2], [4, 10, 1, -99], [122, 123, 106, 105]],
            mask_value=-99,
        )
        d = cfdm.DomainTopology(cell="face", data=data)

        n = np.ma.array([[0, 2, 3, 1], [2, 4, 0, -99], [7, 8, 6, 5]])
        n[1, -1] = np.ma.masked
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

        d.data[:, -1] = np.ma.masked
        n = np.ma.array([[0, 1, 2, -99], [1, 3, 0, -99], [5, 6, 4, -99]])
        n[:, -1] = np.ma.masked

        d0 = d.normalise().array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())

        n = n[:, :-1]
        d0 = d.normalise(remove_empty_columns=True).array
        self.assertEqual(d0.shape, n.shape)
        self.assertTrue((d0.mask == n.mask).all())
        self.assertTrue((d0 == n).all())

        # Point cells
        data = cfdm.Data(
            [[4, 1, 10, 125], [1, 4, -99, -99], [125, 4, -99, -99]],
            mask_value=-99,
        )
        d = cfdm.DomainTopology(cell="point", data=data)

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
