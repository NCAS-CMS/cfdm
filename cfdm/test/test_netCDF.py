import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 3
tmpfiles = [
    tempfile.mkstemp("_test_netCDF.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tempfile1,
    tempfile2,
    tempfile3,
) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class NetCDFTest(unittest.TestCase):
    """Unit test for the NetCDF class."""

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

        nc_group_structure_names = [
            None,
            "/",
            "group/...",
            "group/",
            "group/.../",
            "/group/.../",
        ]
        self.nc_grouped_dimension_names = [
            obj.replace("...", "ncdim")
            for obj in nc_group_structure_names
            if obj is not None
        ]
        self.nc_grouped_variable_names = [
            obj.replace("...", "ncvar")
            for obj in nc_group_structure_names
            if obj is not None
        ]

    def test_netCDF_variable_dimension(self):
        """Test variable and dimension access NetCDF methods."""
        f = cfdm.Field()

        f.nc_set_variable("qwerty")
        self.assertTrue(f.nc_has_variable())
        self.assertEqual(f.nc_get_variable(), "qwerty")
        self.assertEqual(f.nc_get_variable(default=None), "qwerty")
        self.assertEqual(f.nc_del_variable(), "qwerty")
        self.assertFalse(f.nc_has_variable())
        self.assertIsNone(f.nc_get_variable(default=None))
        self.assertIsNone(f.nc_del_variable(default=None))

        f.nc_set_variable("/ncvar")
        self.assertEqual(f.nc_get_variable(), "ncvar")

        f.nc_set_variable("/ncvar/qwerty")
        self.assertEqual(f.nc_get_variable(), "/ncvar/qwerty")

        for nc_var_name in self.nc_grouped_variable_names:
            with self.assertRaises(ValueError):
                f.nc_set_variable(nc_var_name)

        d = cfdm.DomainAxis()

        d.nc_set_dimension("qwerty")
        self.assertTrue(d.nc_has_dimension())
        self.assertEqual(d.nc_get_dimension(), "qwerty")
        self.assertEqual(d.nc_get_dimension(default=None), "qwerty")
        self.assertEqual(d.nc_del_dimension(), "qwerty")
        self.assertFalse(d.nc_has_dimension())
        self.assertIsNone(d.nc_get_dimension(default=None))
        self.assertIsNone(d.nc_del_dimension(default=None))

        d.nc_set_dimension("/ncdim")
        self.assertEqual(d.nc_get_dimension(), "ncdim")

        d.nc_set_dimension("/ncdim/qwerty")
        self.assertEqual(d.nc_get_dimension(), "/ncdim/qwerty")

        for nc_dim_name in self.nc_grouped_dimension_names:
            with self.assertRaises(ValueError):
                d.nc_set_dimension(nc_dim_name)

        d = cfdm.Count()

        d.nc_set_sample_dimension("qwerty")
        self.assertTrue(d.nc_has_sample_dimension())
        self.assertEqual(d.nc_get_sample_dimension(), "qwerty")
        self.assertEqual(d.nc_get_sample_dimension(default=None), "qwerty")
        self.assertEqual(d.nc_del_sample_dimension(), "qwerty")
        self.assertFalse(d.nc_has_sample_dimension())
        self.assertIsNone(d.nc_get_sample_dimension(default=None))
        self.assertIsNone(d.nc_del_sample_dimension(default=None))

        d.nc_set_sample_dimension("/ncdim")
        self.assertEqual(d.nc_get_sample_dimension(), "ncdim")

        d.nc_set_sample_dimension("/ncdim/qwerty")
        self.assertEqual(d.nc_get_sample_dimension(), "/ncdim/qwerty")

        for nc_dim_name in self.nc_grouped_dimension_names:
            with self.assertRaises(ValueError):
                d.nc_set_sample_dimension(nc_dim_name)

        # ------------------------------------------------------------
        # Global attributes
        # ------------------------------------------------------------
        # values keyword
        f = cfdm.Field()

        f.nc_set_global_attribute("Conventions", "CF-1.8")
        f.nc_set_global_attribute("project")
        f.nc_set_global_attribute("foo")
        f.set_property("Conventions", "Y")
        f.set_property("project", "X")
        self.assertEqual(
            f.nc_global_attributes(values=True),
            {"Conventions": "CF-1.8", "project": "X", "foo": None},
        )

        f = cfdm.Field()
        self.assertEqual(f.nc_clear_global_attributes(), {})

        f.nc_set_global_attribute("Conventions")
        f.nc_set_global_attribute("project", "X")
        self.assertEqual(
            f.nc_global_attributes(), {"Conventions": None, "project": "X"}
        )

        f.nc_set_global_attribute("project")
        f.nc_set_global_attribute("comment", None)
        self.assertEqual(
            f.nc_global_attributes(),
            {"Conventions": None, "project": None, "comment": None},
        )

        self.assertEqual(
            f.nc_clear_global_attributes(),
            {"Conventions": None, "project": None, "comment": None},
        )
        self.assertEqual(f.nc_global_attributes(), {})

        f.nc_set_global_attribute("Conventions")
        f.nc_set_global_attribute("project")
        self.assertEqual(
            f.nc_global_attributes(), {"Conventions": None, "project": None}
        )

        _ = f.nc_clear_global_attributes()
        f.nc_set_global_attributes({})
        self.assertEqual(f.nc_global_attributes(), {})

        f.nc_set_global_attributes({"comment": 123}, copy=False)
        self.assertEqual(f.nc_global_attributes(), {"comment": 123})

        f.nc_set_global_attributes({"comment": None, "foo": "bar"})
        self.assertEqual(
            f.nc_global_attributes(), {"comment": None, "foo": "bar"}
        )

        f = cfdm.Field()
        f.set_properties({"foo": "bar", "comment": "variable comment"})
        f.nc_set_variable("tas")
        d = f.set_construct(cfdm.DomainAxis(2))
        f.set_data(cfdm.Data([8, 9]), axes=[d])

        f2 = f.copy()
        f2.nc_set_variable("ua")

        cfdm.write(
            [f, f2],
            tempfile1,
            file_descriptors={"comment": "global comment", "qwerty": "asdf"},
        )

        g = cfdm.read(tempfile1)
        self.assertEqual(len(g), 2)

        for x in g:
            self.assertEqual(
                x.properties(),
                {
                    "comment": "variable comment",
                    "foo": "bar",
                    "qwerty": "asdf",
                    "Conventions": "CF-" + cfdm.CF(),
                },
            )
            self.assertEqual(
                x.nc_global_attributes(),
                {
                    "comment": "global comment",
                    "qwerty": None,
                    "Conventions": None,
                },
            )

        cfdm.write(g, tempfile2)
        h = cfdm.read(tempfile2)
        for x, y in zip(h, g):
            self.assertEqual(x.properties(), y.properties())
            self.assertEqual(
                x.nc_global_attributes(), y.nc_global_attributes()
            )
            self.assertTrue(x.equals(y, verbose=3))
            self.assertTrue(y.equals(x, verbose=3))

        g[1].nc_set_global_attribute("comment", "different comment")
        cfdm.write(g, tempfile3)
        h = cfdm.read(tempfile3)
        for x, y in zip(h, g):
            self.assertEqual(x.properties(), y.properties())
            self.assertEqual(
                x.nc_global_attributes(),
                {"comment": None, "qwerty": None, "Conventions": None},
            )
            self.assertTrue(x.equals(y, verbose=3))
            self.assertTrue(y.equals(x, verbose=3))

    def test_netCDF_geometry_variable(self):
        """Test geometry variable access and (un)setting methods."""
        f = cfdm.Field()

        f.nc_set_geometry_variable("qwerty")
        self.assertTrue(f.nc_has_geometry_variable())
        self.assertEqual(f.nc_get_geometry_variable(), "qwerty")
        self.assertEqual(f.nc_get_geometry_variable(default=None), "qwerty")
        self.assertEqual(f.nc_del_geometry_variable(), "qwerty")
        self.assertFalse(f.nc_has_geometry_variable())
        self.assertIsNone(f.nc_get_geometry_variable(default=None))
        self.assertIsNone(f.nc_del_geometry_variable(default=None))

        f.nc_set_geometry_variable("/ncvar")
        self.assertEqual(f.nc_get_geometry_variable(), "ncvar")

        f.nc_set_geometry_variable("/ncvar/qwerty")
        self.assertEqual(f.nc_get_geometry_variable(), "/ncvar/qwerty")

        for nc_var_name in self.nc_grouped_variable_names:
            with self.assertRaises(ValueError):
                f.nc_set_geometry_variable(nc_var_name)

    def test_netCDF_group_attributes(self):
        """Test group attributes access and (un)setting methods."""
        f = cfdm.Field()

        attrs = f.nc_group_attributes()
        self.assertIsInstance(attrs, dict)
        self.assertFalse(attrs)

        attrs = f.nc_clear_group_attributes()
        self.assertIsInstance(attrs, dict)
        self.assertFalse(attrs)

        attrs = f.nc_group_attributes()
        self.assertIsInstance(attrs, dict)
        self.assertFalse(attrs)

        f.nc_set_group_attributes({"comment": "somthing"})
        attrs = f.nc_group_attributes()
        self.assertEqual(attrs, {"comment": "somthing"})

        attrs = f.nc_clear_group_attributes()
        self.assertEqual(attrs, {"comment": "somthing"})

        attrs = f.nc_group_attributes()
        self.assertIsInstance(attrs, dict)
        self.assertFalse(attrs)

        f.nc_set_group_attributes({"comment": "something"})
        f.nc_set_group_attributes({"foo": "bar"})
        attrs = f.nc_group_attributes()
        self.assertEqual(attrs, {"comment": "something", "foo": "bar"})

        f.nc_clear_group_attributes()
        f.nc_set_group_attribute("foo", "bar")
        attrs = f.nc_group_attributes()
        self.assertEqual(attrs, {"foo": "bar"})
        f.nc_set_group_attribute("foo", "bar2")
        attrs = f.nc_group_attributes()
        self.assertEqual(attrs, {"foo": "bar2"})

        f.set_properties({"prop1": "value1", "comment": "variable comment"})
        f.nc_clear_group_attributes()
        f.nc_set_group_attributes({"comment": None, "foo": "bar"})
        self.assertEqual(
            f.nc_group_attributes(values=True),
            {"comment": "variable comment", "foo": "bar"},
        )

    def test_netCDF_dimension_groups(self):
        """Test dimension groups access and (un)setting methods."""
        d = cfdm.DomainAxis()

        d.nc_set_dimension("ncdim")

        with self.assertRaises(ValueError):
            d.nc_set_dimension_groups(["/forecast"])

        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = d.nc_clear_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        d.nc_set_dimension_groups(["forecast", "model"])
        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))
        self.assertEqual(d.nc_get_dimension(), "/forecast/model/ncdim")

        attrs = d.nc_clear_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)
        self.assertEqual(d.nc_get_dimension(), "ncdim")

        d.nc_set_dimension("ncdim")
        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ())

        d.nc_set_dimension("/ncdim")
        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        d.nc_set_dimension("/forecast/model/ncdim")
        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        d.nc_del_dimension()
        attrs = d.nc_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

    def test_netCDF_variable_groups(self):
        """Test variable groups access and (un)setting methods."""
        f = cfdm.Field()

        f.nc_set_variable("ncdim")

        with self.assertRaises(ValueError):
            f.nc_set_variable_groups(["/forecast"])

        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = f.nc_clear_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        f.nc_set_variable_groups(["forecast", "model"])
        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))
        self.assertEqual(f.nc_get_variable(), "/forecast/model/ncdim")

        attrs = f.nc_clear_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)
        self.assertEqual(f.nc_get_variable(), "ncdim")

        f.nc_set_variable("ncdim")
        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ())

        f.nc_set_variable("/ncdim")
        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        f.nc_set_variable("/forecast/model/ncdim")
        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        f.nc_del_variable()
        attrs = f.nc_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        with self.assertRaises(ValueError):
            f.nc_set_variable_groups(["forecast", "model"])

    def test_netCDF_geometry_variable_groups(self):
        """Test geometry variable groups access NetCDF methods."""
        f = cfdm.Field()

        f.nc_set_geometry_variable("ncvar")

        with self.assertRaises(ValueError):
            f.nc_set_geometry_variable_groups(["/forecast"])

        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = f.nc_clear_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        f.nc_set_geometry_variable_groups(["forecast", "model"])
        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))
        self.assertEqual(f.nc_get_geometry_variable(), "/forecast/model/ncvar")

        attrs = f.nc_clear_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)
        self.assertEqual(f.nc_get_geometry_variable(), "ncvar")

        f.nc_set_geometry_variable("ncvar")
        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ())

        f.nc_set_geometry_variable("/ncvar")
        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        f.nc_set_geometry_variable("/forecast/model/ncvar")
        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        f.nc_del_geometry_variable()
        attrs = f.nc_geometry_variable_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        with self.assertRaises(ValueError):
            f.nc_set_geometry_variable_groups(["forecast", "model"])

    def test_netCDF_sample_dimension_groups(self):
        """Test sample dimension groups access NetCDF methods."""
        c = cfdm.Count()

        c.nc_set_sample_dimension("ncvar")

        with self.assertRaises(ValueError):
            c.nc_set_sample_dimension_groups(["/forecast"])

        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = c.nc_clear_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        c.nc_set_sample_dimension_groups(["forecast", "model"])
        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))
        self.assertEqual(c.nc_get_sample_dimension(), "/forecast/model/ncvar")

        attrs = c.nc_clear_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)
        self.assertEqual(c.nc_get_sample_dimension(), "ncvar")

        c.nc_set_sample_dimension("ncvar")
        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ())

        c.nc_set_sample_dimension("/ncvar")
        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        c.nc_set_sample_dimension("/forecast/model/ncvar")
        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertEqual(attrs, ("forecast", "model"))

        c.nc_del_sample_dimension()
        attrs = c.nc_sample_dimension_groups()
        self.assertIsInstance(attrs, tuple)
        self.assertFalse(attrs)

        with self.assertRaises(ValueError):
            c.nc_set_sample_dimension_groups(["forecast", "model"])

    def test_netCDF_field_components(self):
        """Test field component access and (un)setting methods."""
        # Geometries
        f = cfdm.example_field(6)

        for component in ("interior_ring", "node_count", "part_node_count"):
            f.nc_set_component_variable(component, "ncvar")
            f.nc_set_component_variable_groups(component, ["forecast"])

            f.nc_clear_component_variable_groups(component)
            f.nc_del_component_variable(component)

            f.nc_del_component_variable(component)
            f.nc_clear_component_variable_groups(component)

            f.nc_set_component_variable(component, "ncvar")
            f.nc_set_component_variable_groups(component, ["forecast"])

        for component in ("interior_ring", "part_node_count"):
            f.nc_set_component_dimension(component, "ncvar")
            f.nc_set_component_dimension_groups(component, ["forecast"])

            f.nc_clear_component_dimension_groups(component)
            f.nc_del_component_dimension(component)

            f.nc_del_component_dimension(component)
            f.nc_clear_component_dimension_groups(component)

            f.nc_set_component_dimension(component, "ncvar")
            f.nc_set_component_dimension_groups(component, ["forecast"])

        # Compression: indexed and contiguous
        f = cfdm.example_field(4)
        f.compress("indexed_contiguous", inplace=True)

        for component in ("count", "index"):
            f.nc_set_component_variable(component, "ncvar")
            f.nc_set_component_variable_groups(component, ["forecast"])

            f.nc_clear_component_variable_groups(component)
            f.nc_del_component_variable(component)

            f.nc_del_component_variable(component)
            f.nc_clear_component_variable_groups(component)

            f.nc_set_component_variable(component, "ncvar")
            f.nc_set_component_variable_groups(component, ["forecast"])

        for component in ("count", "index"):
            f.nc_set_component_dimension(component, "ncvar")
            f.nc_set_component_dimension_groups(component, ["forecast"])

            f.nc_clear_component_dimension_groups(component)
            f.nc_del_component_dimension(component)

            f.nc_del_component_dimension(component)
            f.nc_clear_component_dimension_groups(component)

            f.nc_set_component_dimension(component, "ncvar")
            f.nc_set_component_dimension_groups(component, ["forecast"])

        for component in ("count", "index"):
            f.nc_set_component_sample_dimension(component, "ncvar")
            f.nc_set_component_sample_dimension_groups(component, ["forecast"])

            f.nc_clear_component_sample_dimension_groups(component)
            f.nc_del_component_sample_dimension(component)

            f.nc_del_component_sample_dimension(component)
            f.nc_clear_component_sample_dimension_groups(component)

            f.nc_set_component_sample_dimension(component, "ncvar")
            f.nc_set_component_sample_dimension_groups(component, ["forecast"])

        # Compression: gathered
        component = "list"

        # Expected exceptions
        for component in ("list", "node_count"):
            with self.assertRaises(ValueError):
                f.nc_set_component_dimension(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_del_component_dimension(component)

            with self.assertRaises(ValueError):
                f.nc_set_component_dimension_groups(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_clear_component_dimension_groups(component)

            with self.assertRaises(ValueError):
                f.nc_set_component_sample_dimension(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_del_component_sample_dimension(component)

            with self.assertRaises(ValueError):
                f.nc_set_component_sample_dimension_groups(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_clear_component_sample_dimension_groups(component)

        # Expected exceptions
        for component in ("WRONG",):
            with self.assertRaises(ValueError):
                f.nc_set_component_variable(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_del_component_variable(component)

            with self.assertRaises(ValueError):
                f.nc_set_component_variable_groups(component, "ncvar")

            with self.assertRaises(ValueError):
                f.nc_clear_component_variable_groups(component)

    def test_netCDF_to_memory(self):
        """Test the `to_memory` NetCDF method."""
        f = cfdm.example_field(4)
        f.data.to_memory()  # on non-compressed array
        f.compress("indexed_contiguous", inplace=True)
        f.data.to_memory()  # on compressed array


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
