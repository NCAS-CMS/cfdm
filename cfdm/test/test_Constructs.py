import copy
import datetime
import faulthandler
import re
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class ConstructsTest(unittest.TestCase):
    """Unit test for the Constructs class."""

    f = cfdm.example_field(1)
    c = f.constructs

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_Constructs__repr__str__dump(self):
        """Test all means of Constructs inspection."""
        c = self.c

        repr(c)
        str(c)

        c = cfdm.Constructs()
        str(c)

    def test_Constructs__len__(self):
        """Test the length returned for Constructs."""
        c = self.c

        self.assertEqual(len(c), 20)
        self.assertEqual(len(self.f.domain.constructs), 17)

    def test_Constructs_check_construct_type(self):
        """Test the `check_construct_type` Constructs method."""
        c = self.c

        with self.assertRaises(ValueError):
            c._check_construct_type("bad type")

    def test_Constructs_construct_type(self):
        """Test the `construct_type` Constructs method."""
        d = self.f.domain.constructs
        self.assertIsNone(d.construct_type("cell_method"))

    def test_Constructs_construct_types(self):
        """Test the `construct_types` Constructs method."""
        d = self.f.domain.constructs
        self.assertEqual(len(d.construct_types()), len(d))

    def test_Constructs_items_key_value(self):
        """Test the items, key and value Constructs methods."""
        c = self.c

        for i, (key, value) in enumerate(c.items()):
            x = c.filter_by_key(key)
            self.assertEqual(x.key(), key)
            self.assertIs(x.value(), value)

        self.assertEqual(i, 19)

    def test_Constructs_copy_shallow_copy(self):
        """Test the Constructs methods for copying."""
        c = self.c

        d = c.filter_by_type("domain_axis")
        e = d.copy()

        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

        d = c.shallow_copy()
        self.assertTrue(c.equals(d, verbose=3))
        self.assertTrue(d.equals(c, verbose=3))

    def test_Constructs_domain_axis_identity(self):
        """Test the `domain_axis_identity` Constructs method."""
        c = self.c

        with self.assertRaises(ValueError):
            c.domain_axis_identity(999)

    def test_Constructs_filter(self):
        """Trivial test of constructs-filtering Constructs methods."""
        c = self.c

        for todict in (False, True):
            d = c.filter(
                filter_by_axis=(),
                filter_by_data=True,
                filter_by_identity=(),
                filter_by_key=(),
                filter_by_measure=(),
                filter_by_method=(),
                filter_by_naxes=(),
                filter_by_ncdim=(),
                filter_by_ncvar=(),
                filter_by_property={},
                filter_by_size=(),
                filter_by_type=(),
                todict=todict,
            )
            self.assertEqual(len(d), 0)

        self.assertEqual(c.filter(cached=999), 999)
        self.assertTrue(c.filter().equals(c))

        with self.assertRaises(TypeError):
            c.filter(bad_kwarg=None)

    def test_Constructs_FILTERING(self):
        """Test Constructs methods that invert or reverse filters."""
        c = self.c

        # Axis
        for axis_mode in ("and", "or", "exact", "subset"):
            for args in (
                ["qwerty"],
                ["domainaxis0"],
                ["domainaxis0", "domainaxis1"],
                ["domainaxis0", "domainaxis1", "domainaxis2"],
            ):
                d = c.filter_by_axis(*args, axis_mode=axis_mode)
                e = d.inverse_filter()
                self.assertEqual(len(e), len(c) - len(d))

        # Inverse filter, filters applied
        self.assertEqual(len(c.filters_applied()), 0)
        ci = c.inverse_filter()
        self.assertEqual(len(ci), 0)
        self.assertEqual(len(ci), len(c) - len(c))

        d = c.filter_by_type("dimension_coordinate", "auxiliary_coordinate")
        self.assertEqual(len(d.filters_applied()), 1)
        di = d.inverse_filter()
        self.assertEqual(len(di), len(c) - len(d))

        e = d.filter_by_property(units="degrees")
        self.assertEqual(len(e.filters_applied()), 2)
        ei = e.inverse_filter(1)
        self.assertEqual(len(e.filters_applied()), 2)
        self.assertEqual(len(ei), len(d) - len(e))

        d2 = c.filter_by_type("auxiliary_coordinate")
        e2 = d2.filter_by_naxes(1)
        f2 = e2.inverse_filter(1)
        g2 = f2.inverse_filter(1)
        h2 = g2.inverse_filter(1)
        self.assertTrue(g2.equals(e2, verbose=3))
        self.assertTrue(h2.equals(f2, verbose=3))

        # Unfilter
        self.assertTrue(e.unfilter(1).equals(d, verbose=3))
        self.assertTrue(e.unfilter(1).unfilter().equals(c, verbose=3))
        self.assertTrue(d.unfilter(1).equals(c, verbose=3))
        self.assertTrue(c.unfilter(1).equals(c, verbose=3))

    def test_Constructs_domain_axes(self):
        """Test the `domain_axes` Constructs method."""
        c = self.c

        self.assertEqual(c.domain_axes(cached=999), 999)
        self.assertEqual(
            len(c.domain_axes(filter_by_identity=("grid_longitude",))), 1
        )

        keys = tuple(c.domain_axes(todict=True))
        self.assertEqual(len(c.domain_axes(*keys)), 4)
        self.assertEqual(len(c.domain_axes(keys)), 0)

        with self.assertRaises(TypeError):
            c.domain_axes(filter_by_type=("dimension_coordinate",))

        with self.assertRaises(TypeError):
            c.domain_axes(
                "grid_latitude", filter_by_identity=("grid_longitude",)
            )

    def test_Constructs_filter_by_data(self):
        """Test the `filter_by_data` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_data()), 12)
        self.assertEqual(c.filter_by_data(cached=999), 999)

    def test_Constructs_filter_by_type(self):
        """Test the `filter_by_type` Constructs method."""
        c = self.c

        self.assertEqual(c.filter_by_type(cached=999), 999)

        d = c.filter(
            filter_by_property={"standard_name": None},
            filter_by_type=("dimension_coordinate",),
            todict=True,
        )
        self.assertEqual(len(d), 4)

        constructs = c.filter_by_type(
            "auxiliary_coordinate",
            "cell_measure",
            "cell_method",
            "coordinate_reference",
            "dimension_coordinate",
            "domain_ancillary",
            "domain_axis",
            "field_ancillary",
        )
        n = 20
        self.assertEqual(len(constructs), n)

        constructs = c.filter_by_type("auxiliary_coordinate")
        n = 3
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.AuxiliaryCoordinate)

        constructs = c.filter_by_type("cell_measure")
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMeasure)

        constructs = c.filter_by_type("cell_method")
        n = 2
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMethod)

        constructs = c.filter_by_type("dimension_coordinate")
        n = 4
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DimensionCoordinate)

        constructs = c.filter_by_type("coordinate_reference")
        n = 2
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CoordinateReference)

        constructs = c.filter_by_type("domain_ancillary")
        n = 3
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = c.filter_by_type("field_ancillary")
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.FieldAncillary)

        constructs = c.filter_by_type("domain_axis")
        n = 4
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

        constructs = c.filter_by_type(*["domain_ancillary"])
        n = 3
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = c.filter_by_type("domain_ancillary", "domain_axis")
        n = 7
        self.assertEqual(len(constructs), n)

        self.assertEqual(len(c.filter_by_type("qwerty")), 0)

    def test_Constructs_filter_by_method(self):
        """Test the `filter_by_method` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_method()), 2)
        self.assertEqual(len(c.filter_by_method("mean")), 1)
        self.assertEqual(len(c.filter_by_method("qwerty")), 0)
        self.assertEqual(c.filter_by_method(cached=999), 999)

    def test_Constructs_filter_by_ncdim(self):
        """Test the `filter_by_ncdim` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_ncdim()), 4)
        self.assertEqual(len(c.filter_by_ncdim("y")), 1)
        self.assertEqual(len(c.filter_by_ncdim("qwerty")), 0)
        self.assertEqual(c.filter_by_ncdim(cached=999), 999)

    def test_Constructs_filter_by_ncvar(self):
        """Test the `filter_by_ncvar` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_ncvar()), 14)
        self.assertEqual(len(c.filter_by_ncvar("qwerty")), 0)
        self.assertEqual(len(c.filter_by_ncvar("a")), 1)
        self.assertEqual(c.filter_by_ncvar(cached=999), 999)

    def test_Constructs_filter_by_measure(self):
        """Test the `filter_by_measure` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_measure()), 1)
        self.assertEqual(len(c.filter_by_measure("qwerty")), 0)
        self.assertEqual(len(c.filter_by_measure("area")), 1)
        self.assertEqual(c.filter_by_measure(cached=999), 999)

    def test_Constructs_filter_by_identity(self):
        """Test the `filter_by_identity` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_identity()), 20)
        self.assertEqual(len(c.filter_by_identity("qwerty")), 0)
        self.assertEqual(len(c.filter_by_identity("latitude")), 1)
        self.assertEqual(c.filter_by_identity(cached=999), 999)

        self.assertEqual(
            len(c.filter_by_identity("dimensioncoordinate1", "longitude")), 2
        )

        with self.assertRaises(TypeError):
            c("latitude", filter_by_identity=("longitude",))

    def test_Constructs_filter_by_axis(self):
        """Test the `filter_by_axis` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_axis()), 12)
        self.assertEqual(len(c.filter_by_axis(0, 1, 2, axis_mode="or")), 11)
        self.assertEqual(
            len(c.filter_by_axis("domainaxis1", axis_mode="or")), 7
        )
        self.assertEqual(len(c.filter_by_axis("grid_longitude")), 6)
        self.assertEqual(len(c.filter_by_axis(re.compile("^grid_lon"))), 6)
        self.assertEqual(len(c.filter_by_axis(re.compile("^grid"))), 0)
        self.assertEqual(len(c.filter_by_axis("ncdim%x")), 6)

        self.assertEqual(c.filter_by_axis(cached=999), 999)

        self.assertEqual(len(c.filter_by_axis(99)), 0)
        self.assertEqual(len(c.filter_by_axis(99, todict=True)), 0)

        with self.assertRaises(ValueError):
            c.filter_by_axis(0, 1, axis_mode="bad_mode")

    def test_Constructs_clear_filters_applied(self):
        """Test the `clear_filters_applied` Constructs method."""
        c = self.c

        d = c.shallow_copy()
        d.clear_filters_applied()

    def test_Constructs_filter_by_naxes(self):
        """Test the `filter_by_naxes` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_naxes()), 12)
        self.assertEqual(len(c.filter_by_naxes(1)), 7)
        self.assertEqual(c.filter_by_naxes(cached=999), 999)

    def test_Constructs_filter_by_property(self):
        """Test the `filter_by_property` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_property()), 12)

        for mode in ([], ["and"], ["or"]):
            for kwargs in (
                {"qwerty": 34},
                {"standard_name": "surface_altitude"},
                {"standard_name": "surface_altitude", "units": "m"},
                {"standard_name": "surface_altitude", "units": "degrees"},
                {"standard_name": "surface_altitude", "units": "qwerty"},
            ):
                d = c.filter_by_property(*mode, **kwargs)
                e = d.inverse_filter()
                self.assertEqual(len(e), len(c) - len(d))

        self.assertEqual(len(c.filter_by_property(standard_name=None)), 8)

        with self.assertRaises(ValueError):
            c.filter_by_property("too many", "modes")

        with self.assertRaises(ValueError):
            c.filter_by_property("bad_mode")

    def test_Constructs_filter_by_size(self):
        """Test the `filter_by_size` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_size(9)), 1)
        self.assertEqual(len(c.filter_by_size(9, 10)), 2)
        self.assertEqual(len(c.filter_by_size()), 4)
        self.assertEqual(len(c.filter_by_size(-1)), 0)
        self.assertEqual(c.filter_by_size(cached=999), 999)

    def test_Constructs_filter_by_key(self):
        """Test the `filter_by_key` Constructs method."""
        c = self.c

        self.assertEqual(len(c.filter_by_key()), 20)
        self.assertEqual(len(c.filter_by_key("qwerty")), 0)
        self.assertEqual(len(c.filter_by_key("dimensioncoordinate1")), 1)
        self.assertEqual(len(c.filter_by_key(re.compile("^dim"))), 4)
        self.assertEqual(c.filter_by_key(cached=999), 999)

    def test_Constructs_copy(self):
        """Test the copy module copying behaviour of Constructs."""
        c = self.c

        copy.copy(c)
        copy.deepcopy(c)

    def test_Constructs__getitem__(self):
        """Test the lookup access of construct items from Constructs."""
        c = self.c

        self.assertIsInstance(
            c["auxiliarycoordinate1"], cfdm.AuxiliaryCoordinate
        )

        with self.assertRaises(KeyError):
            c["bad_key"]

    def test_Constructs_get_data_axes(self):
        """Test the `get_data_axes` Constructs method."""
        c = self.c

        with self.assertRaises(ValueError):
            c.get_data_axes("bad key")

    def test_Constructs_todict(self):
        """Test the todict Constructs method."""
        c = self.c

        self.assertIsInstance(c.todict(), dict)

    def test_Constructs_private(self):
        """Test internal (designated as private) Constructs methods."""
        c = self.f.domain.constructs

        # _construct_type_description
        self.assertEqual(
            c._construct_type_description("auxiliary_coordinate"),
            "auxiliary coordinate",
        )

        # _check_construct_type
        self.assertIsNone(c._check_construct_type(None))
        self.assertIsNone(c._check_construct_type("cell_method", None))

        x = c.shallow_copy()
        del x._constructs["auxiliary_coordinate"]
        with self.assertRaises(KeyError):
            x["auxiliarycoordinate1"]

        # _del_construct
        x = self.c.shallow_copy()
        x._del_construct("domainancillary0")

        with self.assertRaises(ValueError):
            x._del_construct("domainaxis1")

        x._del_construct("dimensioncoordinate3")
        with self.assertRaises(ValueError):
            x._del_construct("domainaxis3")

        x = c.shallow_copy()
        x._del_construct("dimensioncoordinate3")
        self.assertIsInstance(x._del_construct("domainaxis3"), cfdm.DomainAxis)

        # _set_construct
        x = self.c.shallow_copy()
        with self.assertRaises(ValueError):
            x._set_construct(
                self.f.construct("cellmethod0"), axes=["domainaxis0"]
            )

        # _set_construct_data_axes
        x = self.c.shallow_copy()
        with self.assertRaises(ValueError):
            x._set_construct_data_axes("qwerty", ["domainaxis"])

        with self.assertRaises(ValueError):
            x._set_construct_data_axes("auxiliarycoordinate1", ["qwerty"])

        with self.assertRaises(ValueError):
            x._set_construct_data_axes("auxiliarycoordinate1", ["domainaxis0"])

        # _pop
        x = c.shallow_copy()
        with self.assertRaises(KeyError):
            x._pop("qwerty")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
