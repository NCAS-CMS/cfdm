import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

import netCDF4
import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 2
tmpfiles = [
    tempfile.mkstemp("_test_geometry.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tempfile, tempfile2) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


VN = cfdm.CF()


class GeometryTest(unittest.TestCase):
    """Test the management of geometry cells."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.geometry_1_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "geometry_1.nc"
        )
        self.geometry_2_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "geometry_2.nc"
        )
        self.geometry_3_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "geometry_3.nc"
        )
        self.geometry_4_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "geometry_4.nc"
        )
        self.geometry_interior_ring_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "geometry_interior_ring.nc",
        )
        self.geometry_interior_ring_file_2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "geometry_interior_ring_2.nc",
        )

    def test_node_count(self):
        """Test geometry coordinate node count variables."""
        f = cfdm.read(self.geometry_1_file)

        self.assertEqual(len(f), 2)
        for g in f:
            self.assertTrue(g.equals(g.copy()))
            self.assertEqual(len(g.auxiliary_coordinates()), 2)

        g = f[0]
        for axis in ("X", "Y"):
            coord = g.construct("axis=" + axis)
            self.assertTrue(coord.has_node_count())
            self.assertFalse(coord.has_part_node_count())
            self.assertFalse(coord.has_interior_ring())

        cfdm.write(f, tempfile, Conventions="CF-" + VN)

        f2 = cfdm.read(tempfile)
        self.assertEqual(len(f2), 2)
        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b))

        # Setting of node count properties
        coord = f[0].construct("axis=X")
        nc = coord.get_node_count()
        cfdm.write(f, tempfile)
        nc.set_property("long_name", "Node counts")
        cfdm.write(f, tempfile)
        nc.nc_set_variable("new_var_name_X")
        cfdm.write(f, tempfile)

        # Node count access
        c = g.construct("longitude").copy()
        self.assertTrue(c.has_node_count())
        n = c.del_node_count()
        self.assertFalse(c.has_node_count())
        self.assertIsNone(c.get_node_count(None))
        self.assertIsNone(c.del_node_count(None))
        c.set_node_count(n)
        self.assertTrue(c.has_node_count())
        self.assertTrue(c.get_node_count(None).equals(n))
        self.assertTrue(c.del_node_count(None).equals(n))
        self.assertFalse(c.has_node_count())

    def test_geometry_2(self):
        """Test nodes not tied to auxiliary coordinate variables."""
        f = cfdm.read(self.geometry_2_file)

        self.assertEqual(len(f), 2)

        for g in f:
            self.assertTrue(g.equals(g.copy()))
            self.assertEqual(len(g.auxiliary_coordinates()), 3)

        g = f[0]
        for axis in ("X", "Y", "Z"):
            coord = g.construct("axis=" + axis)
            self.assertTrue(coord.has_node_count())
            self.assertFalse(coord.has_part_node_count())
            self.assertFalse(coord.has_interior_ring())

        cfdm.write(f, tempfile, Conventions="CF-" + VN)

        f2 = cfdm.read(tempfile)

        self.assertEqual(len(f2), 2)

        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b))

        # Setting of node count properties
        coord = f[0].construct("axis=X")
        nc = coord.get_node_count()
        cfdm.write(f, tempfile)
        nc.set_property("long_name", "Node counts")
        cfdm.write(f, tempfile)
        nc.nc_set_variable("new_var_name")
        cfdm.write(f, tempfile)

    def test_geometry_3(self):
        """Test nodes in a file with no node count variable."""
        f = cfdm.read(self.geometry_3_file)

        self.assertEqual(len(f), 2)

        for g in f:
            self.assertTrue(g.equals(g.copy()))
            self.assertEqual(len(g.auxiliary_coordinates()), 3)

        g = f[0]
        for axis in ("X", "Y", "Z"):
            coord = g.construct("axis=" + axis)
            self.assertFalse(coord.has_node_count())
            self.assertFalse(coord.has_part_node_count())
            self.assertFalse(coord.has_interior_ring())

        cfdm.write(f, tempfile, Conventions="CF-" + VN)

        f2 = cfdm.read(tempfile)

        self.assertEqual(len(f2), 2)

        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b))

    def test_geometry_4(self):
        """Test nodes all not tied to auxiliary coordinate variables."""
        f = cfdm.read(self.geometry_4_file)

        self.assertEqual(len(f), 2)

        for g in f:
            self.assertTrue(g.equals(g.copy()))
            self.assertEqual(len(g.auxiliary_coordinates()), 3)

        for axis in ("X", "Y"):
            coord = g.construct("axis=" + axis)
            self.assertTrue(coord.has_node_count())
            self.assertFalse(coord.has_part_node_count())
            self.assertFalse(coord.has_interior_ring())

        cfdm.write(f, tempfile, Conventions="CF-" + VN)

        f2 = cfdm.read(tempfile)

        self.assertEqual(len(f2), 2)

        for a, b in zip(f, f2):
            self.assertTrue(a.equals(b))

        # Setting of node count properties
        coord = f[0].construct("axis=X")
        nc = coord.get_node_count()
        cfdm.write(f, tempfile)
        nc.set_property("long_name", "Node counts")
        cfdm.write(f, tempfile)
        nc.nc_set_variable("new_var_name")
        cfdm.write(f, tempfile)

    def test_geometry_multipart_order(self):
        """Test that multipart polygon nodes retain their geometry order."""
        # Four polygons, each with two disjoint anticlockwise triangles.
        x = np.array(
            [a + 30 * i for i in range(4) for a in (20, 10, 0, 20, 10, 0)]
        )
        y = np.array([0, 15, 0, 20, 35, 20] * 4)

        with netCDF4.Dataset(tempfile, "w") as nc:
            nc.Conventions = "CF-" + VN
            for name, size in (("node", 24), ("instance", 4), ("part", 8)):
                nc.createDimension(name, size)

            for name, nodes, standard_name, units, axis in (
                ("x", x, "longitude", "degrees_east", "X"),
                ("y", y, "latitude", "degrees_north", "Y"),
            ):
                v = nc.createVariable(name, "f8", ("node",))
                v.setncatts(
                    dict(standard_name=standard_name, units=units, axis=axis)
                )
                v[:] = nodes

            v = nc.createVariable("node_count", "i4", ("instance",))
            v[:] = [6] * 4
            v = nc.createVariable("part_node_count", "i4", ("part",))
            v[:] = [3] * 8
            v = nc.createVariable("geometry_container", "i4", ())
            v.setncatts(
                dict(
                    geometry_type="polygon",
                    node_coordinates="x y",
                    node_count="node_count",
                    part_node_count="part_node_count",
                )
            )
            v = nc.createVariable("value", "f8", ("instance",))
            v.setncatts(dict(units="1", geometry="geometry_container"))
            v[:] = [1, 2, 3, 4]

        for backend in (None, "netCDF4", "h5py"):
            with self.subTest(backend=backend):
                (f,) = cfdm.read(tempfile, backend=backend)
                for name, nodes in (("longitude", x), ("latitude", y)):
                    np.testing.assert_array_equal(
                        f.construct(name).bounds.array, nodes.reshape(4, 2, 3)
                    )

                cfdm.write(f, tempfile2)
                with netCDF4.Dataset(tempfile2) as nc:
                    geometry = nc.variables[nc.variables["value"].geometry]
                    for axis, nodes in (("X", x), ("Y", y)):
                        v = next(
                            nc.variables[name]
                            for name in geometry.node_coordinates.split()
                            if nc.variables[name].axis == axis
                        )
                        np.testing.assert_array_equal(v[:], nodes)

    def test_geometry_interior_ring(self):
        """Test the management of interior ring geometries."""
        for geometry_file in (
            self.geometry_interior_ring_file,
            self.geometry_interior_ring_file_2,
        ):
            f = cfdm.read(geometry_file)

            self.assertEqual(len(f), 2)

            for g in f:
                self.assertTrue(g.equals(g.copy()))
                self.assertEqual(len(g.auxiliary_coordinates()), 4)

            g = f[0]
            for axis in ("X", "Y"):
                coord = g.construct("axis=" + axis)
                self.assertTrue(coord.has_node_count())
                self.assertTrue(coord.has_part_node_count())
                self.assertTrue(coord.has_interior_ring())

            cfdm.write(f, tempfile, Conventions="CF-" + VN)

            f2 = cfdm.read(tempfile)

            self.assertEqual(len(f2), 2)

            for a, b in zip(f, f2):
                self.assertTrue(a.equals(b))

            # Interior ring component
            c = g.construct("longitude")

            self.assertTrue(
                c.interior_ring.equals(
                    g.construct("longitude").get_interior_ring()
                )
            )
            self.assertEqual(c.interior_ring.data.ndim, c.data.ndim + 1)
            self.assertEqual(c.interior_ring.data.shape[0], c.data.shape[0])

            self.assertIsInstance(g.dump(display=False), str)

            d = c.insert_dimension(0)
            self.assertEqual(d.data.shape, (1,) + c.data.shape)
            self.assertEqual(
                d.interior_ring.data.shape, (1,) + c.interior_ring.data.shape
            )

            e = d.squeeze(0)
            self.assertEqual(e.data.shape, c.data.shape)
            self.assertEqual(
                e.interior_ring.data.shape, c.interior_ring.data.shape
            )

            t = d.transpose()
            self.assertEqual(
                t.data.shape,
                d.data.shape[::-1],
                (t.data.shape, c.data.shape[::-1]),
            )
            self.assertEqual(
                t.interior_ring.data.shape,
                (
                    d.interior_ring.data.shape[-2::-1]
                    + (d.interior_ring.data.shape[-1],)
                ),
            )

            # Subspacing
            g = g[1, ...]
            c = g.construct("longitude")
            self.assertEqual(c.interior_ring.data.shape[0], 1)
            self.assertEqual(c.interior_ring.data.ndim, c.data.ndim + 1)
            self.assertEqual(c.interior_ring.data.shape[0], c.data.shape[0])

            # Setting of node count properties
            coord = f[0].construct("axis=Y")
            nc = coord.get_node_count()
            nc.set_property("long_name", "Node counts")
            cfdm.write(f, tempfile)

            nc.nc_set_variable("new_var_name")
            cfdm.write(f, tempfile)

            # Setting of part node count properties
            coord = f[0].construct("axis=X")
            pnc = coord.get_part_node_count()
            pnc.set_property("long_name", "Part node counts")
            cfdm.write(f, tempfile)

            pnc.nc_set_variable("new_var_name")
            cfdm.write(f, tempfile)

            pnc.nc_set_dimension("new_dim_name")
            cfdm.write(f, tempfile)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
