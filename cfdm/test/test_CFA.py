import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest
from pathlib import PurePath

import netCDF4

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 4
tmpfiles = [
    tempfile.mkstemp("_test_CFA.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tmpfile1,
    tmpfile2,
    nc_file,
    cfa_file,
) = tmpfiles


def _remove_tmpfiles():
    """Try to remove defined temporary files by deleting their paths."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class CFATest(unittest.TestCase):
    netcdf3_fmts = [
        "NETCDF3_CLASSIC",
        "NETCDF3_64BIT",
        "NETCDF3_64BIT_OFFSET",
        "NETCDF3_64BIT_DATA",
    ]
    netcdf4_fmts = ["NETCDF4", "NETCDF4_CLASSIC"]
    netcdf_fmts = netcdf3_fmts + netcdf4_fmts

    def test_CFA_fmt(self):
        """Test the cfdm.read 'fmt' and 'cfa' keywords."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        for fmt in self.netcdf_fmts:
            cfdm.write(f, cfa_file, fmt=fmt, cfa=True)
            g = cfdm.read(cfa_file)
            self.assertEqual(len(g), 1)
            self.assertTrue(f.equals(g[0]))

    def test_CFA_multiple_fragments(self):
        """Test aggregation variables with more than one fragment."""
        f = cfdm.example_field(0)

        cfdm.write(f[:2], tmpfile1)
        cfdm.write(f[2:], tmpfile2)

        a = cfdm.read(tmpfile1)[0]
        b = cfdm.read(tmpfile2)[0]
        a = cfdm.Field.concatenate([a, b], axis=0)

        cfdm.write(a, nc_file)
        cfdm.write(a, cfa_file, cfa=True)

        n = cfdm.read(nc_file)
        c = cfdm.read(cfa_file)
        self.assertEqual(len(n), 1)
        self.assertEqual(len(c), 1)
        self.assertTrue(c[0].equals(f))
        self.assertTrue(n[0].equals(c[0]))

    def test_CFA_strict(self):
        """Test 'strict' option to the cfdm.write 'cfa' keyword."""
        f = cfdm.example_field(0)

        # By default, can't write in-memory arrays as aggregation
        # variables
        with self.assertRaises(ValueError):
            cfdm.write(f, cfa_file, cfa=True)

        # The previous line should have deleted the output file
        self.assertFalse(os.path.exists(cfa_file))

        cfdm.write(f, nc_file, cfa={"strict": False})
        g = cfdm.read(nc_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(g[0].equals(f))

        cfdm.write(g, cfa_file, cfa={"strict": True})
        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(g[0].equals(f))

    def test_CFA_substitutions_0(self):
        """Test aggregation substitution URI substitutions (0)."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        cwd = os.getcwd()
        f.data.nc_update_aggregated_substitutions({"base": cwd})

        cfdm.write(
            f,
            cfa_file,
            cfa={"absolute_paths": True},
        )

        nc = netCDF4.Dataset(cfa_file, "r")
        cfa_location = nc.variables["cfa_location"]
        self.assertEqual(
            cfa_location.getncattr("substitutions"),
            f"${{base}}: {cwd}",
        )
        self.assertEqual(
            cfa_location[...], f"file://${{base}}/{os.path.basename(tmpfile1)}"
        )
        nc.close()

        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(f.equals(g[0], verbose=-1))

    def test_CFA_substitutions_1(self):
        """Test aggregation substitution URI substitutions (1)."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        cwd = os.getcwd()
        for base in ("base", "${base}"):
            cfdm.write(
                f,
                cfa_file,
                cfa={"absolute_paths": True, "substitutions": {base: cwd}},
            )

            nc = netCDF4.Dataset(cfa_file, "r")
            cfa_location = nc.variables["cfa_location"]
            self.assertEqual(
                cfa_location.getncattr("substitutions"),
                f"${{base}}: {cwd}",
            )
            self.assertEqual(
                cfa_location[...],
                f"file://${{base}}/{os.path.basename(tmpfile1)}",
            )
            nc.close()

        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(f.equals(g[0], verbose=-1))

    def test_CFA_substitutions_2(self):
        """Test aggregation substitution URI substitutions (2)."""
        f = cfdm.example_field(0)
        tmpfile1 = "tmpfile1.nc"
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        cwd = os.getcwd()

        f.data.nc_clear_aggregated_substitutions()
        f.data.nc_update_aggregated_substitutions({"base": cwd})
        cfa_file = "cfa_file.nc"
        cfdm.write(
            f,
            cfa_file,
            cfa={
                "absolute_paths": True,
                "substitutions": {"base2": "/bad/location"},
            },
        )

        nc = netCDF4.Dataset(cfa_file, "r")
        cfa_location = nc.variables["cfa_location"]
        self.assertEqual(
            cfa_location.getncattr("substitutions"),
            f"${{base2}}: /bad/location ${{base}}: {cwd}",
        )
        self.assertEqual(
            cfa_location[...], f"file://${{base}}/{os.path.basename(tmpfile1)}"
        )
        nc.close()

        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(f.equals(g[0]))

        f.data.nc_clear_aggregated_substitutions()
        f.data.nc_update_aggregated_substitutions({"base": "/bad/location"})

        cfdm.write(
            f,
            cfa_file,
            cfa={"absolute_paths": True, "substitutions": {"base": cwd}},
        )

        nc = netCDF4.Dataset(cfa_file, "r")
        cfa_location = nc.variables["cfa_location"]
        self.assertEqual(
            cfa_location.getncattr("substitutions"),
            f"${{base}}: {cwd}",
        )
        self.assertEqual(
            cfa_location[...], f"file://${{base}}/{os.path.basename(tmpfile1)}"
        )
        nc.close()

        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(f.equals(g[0]))

        f.data.nc_clear_aggregated_substitutions()
        f.data.nc_update_aggregated_substitutions({"base2": "/bad/location"})

        cfdm.write(
            f,
            cfa_file,
            cfa={"absolute_paths": True, "substitutions": {"base": cwd}},
        )

        nc = netCDF4.Dataset(cfa_file, "r")
        cfa_location = nc.variables["cfa_location"]
        self.assertEqual(
            cfa_location.getncattr("substitutions"),
            f"${{base2}}: /bad/location ${{base}}: {cwd}",
        )
        self.assertEqual(
            cfa_location[...], f"file://${{base}}/{os.path.basename(tmpfile1)}"
        )
        nc.close()

        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        self.assertTrue(f.equals(g[0]))

    def test_CFA_absolute_paths(self):
        """Test aggregation 'absolute_paths' option to the cfa.write
        'cfa' keyword."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        for absolute_paths, filename in zip(
            (True, False),
            (
                PurePath(os.path.abspath(tmpfile1)).as_uri(),
                os.path.basename(tmpfile1),
            ),
        ):
            cfdm.write(f, cfa_file, cfa={"absolute_paths": absolute_paths})

            nc = netCDF4.Dataset(cfa_file, "r")
            cfa_location = nc.variables["cfa_location"]
            self.assertEqual(cfa_location[...], filename)
            nc.close()

            g = cfdm.read(cfa_file)
            self.assertEqual(len(g), 1)
            self.assertTrue(f.equals(g[0]))

    def test_CFA_constructs(self):
        """Test choice of constructs to write as aggregation
        variables."""
        f = cfdm.example_field(1)
        f.del_construct("time")
        f.del_construct("long_name=Grid latitude name")
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]

        # No constructs
        cfdm.write(f, tmpfile2, cfa={"constructs": []})
        nc = netCDF4.Dataset(tmpfile2, "r")
        for var in nc.variables.values():
            attrs = var.ncattrs()
            self.assertNotIn("aggregated_dimensions", attrs)
            self.assertNotIn("aggregated_data", attrs)

        nc.close()

        # Field construct
        cfdm.write(f, tmpfile2, cfa={"constructs": "field"})
        nc = netCDF4.Dataset(tmpfile2, "r")
        for ncvar, var in nc.variables.items():
            attrs = var.ncattrs()
            if ncvar in ("ta",):
                self.assertFalse(var.ndim)
                self.assertIn("aggregated_dimensions", attrs)
                self.assertIn("aggregated_data", attrs)
            else:
                self.assertNotIn("aggregated_dimensions", attrs)
                self.assertNotIn("aggregated_data", attrs)

        nc.close()

        # Dimension construct
        for constructs in (
            "dimension_coordinate",
            ["dimension_coordinate"],
            {"dimension_coordinate": None},
            {"dimension_coordinate": 1},
        ):
            cfdm.write(f, tmpfile2, cfa={"constructs": constructs})
            nc = netCDF4.Dataset(tmpfile2, "r")
            for ncvar, var in nc.variables.items():
                attrs = var.ncattrs()
                if ncvar in (
                    "x",
                    "x_bnds",
                    "y",
                    "y_bnds",
                    "atmosphere_hybrid_height_coordinate",
                    "atmosphere_hybrid_height_coordinate_bounds",
                ):
                    self.assertFalse(var.ndim)
                    self.assertIn("aggregated_dimensions", attrs)
                    self.assertIn("aggregated_data", attrs)
                else:
                    self.assertNotIn("aggregated_dimensions", attrs)
                    self.assertNotIn("aggregated_data", attrs)

            nc.close()

        # Dimension and auxiliary constructs
        for constructs in (
            ["dimension_coordinate", "auxiliary_coordinate"],
            {"dimension_coordinate": None, "auxiliary_coordinate": 2},
        ):
            cfdm.write(f, tmpfile2, cfa={"constructs": constructs})
            nc = netCDF4.Dataset(tmpfile2, "r")
            for ncvar, var in nc.variables.items():
                attrs = var.ncattrs()
                if ncvar in (
                    "x",
                    "x_bnds",
                    "y",
                    "y_bnds",
                    "atmosphere_hybrid_height_coordinate",
                    "atmosphere_hybrid_height_coordinate_bounds",
                    "latitude_1",
                    "longitude_1",
                ):
                    self.assertFalse(var.ndim)
                    self.assertIn("aggregated_dimensions", attrs)
                    self.assertIn("aggregated_data", attrs)
                else:
                    self.assertNotIn("aggregated_dimensions", attrs)
                    self.assertNotIn("aggregated_data", attrs)

            nc.close()

    def test_CFA_multiple_files(self):
        """Test storing multiple locations for the same fragment."""
        f = cfdm.example_field(0)
        cfdm.write(f, tmpfile1)
        f = cfdm.read(tmpfile1)[0]
        f.add_file_directory("/new/path")

        cfdm.write(f, cfa_file, cfa=True)
        g = cfdm.read(cfa_file)
        self.assertEqual(len(g), 1)
        g = g[0]
        self.assertTrue(f.equals(g))

        self.assertEqual(len(g.data.get_filenames()), 2)
        self.assertEqual(len(g.get_filenames()), 3)

    def test_CFA_unlimited_dimension(self):
        """Test aggregation files with unlimited dimensions."""
        # Create an aggregation file from a field that has an
        # unlimited dimension and no metadata constructs spanning that
        # dimension
        f = cfdm.example_field(0)
        axis = f.domain_axis("longitude")
        axis.nc_set_unlimited(True)
        f.del_construct("longitude")
        cfdm.write(f, tmpfile1)
        g = cfdm.read(tmpfile1)
        cfdm.write(g, tmpfile2, cfa=True)

        # Check that the aggregation file can be read
        h = cfdm.read(tmpfile2)
        self.assertEqual(len(h), 1)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
