import copy
import datetime
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class ConstructsTest(unittest.TestCase):
    """TODO DOCS."""

    f = cfdm.example_field(1)

    def setUp(self):
        """TODO DOCS."""
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
        """TODO DOCS."""
        f = self.f

        c = f.constructs
        repr(c)
        str(c)

    def test_Constructs_key_items_value(self):
        """TODO DOCS."""
        f = self.f

        for key, value in f.constructs.items():
            x = f.constructs.filter_by_key(key)
            self.assertEqual(x.key(), key)
            self.assertTrue(x.value().equals(value))

    def test_Constructs_copy_shallow_copy(self):
        """TODO DOCS."""
        c = self.f.constructs

        d = c.copy()
        self.assertTrue(c.equals(d, verbose=3))
        self.assertTrue(d.equals(c, verbose=3))

        d = c.shallow_copy()
        self.assertTrue(c.equals(d, verbose=3))
        self.assertTrue(d.equals(c, verbose=3))

    def test_Constructs_filter(self):
        """TODO DOCS."""
        c = self.f.constructs

        for todict in (False, True):
            d = c.filter(
                filter_by_axis=(),
                filter_by_data=(),
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

    def test_Constructs_FILTERING(self):
        """TODO DOCS."""
        c = self.f.constructs

        self.assertEqual(len(c), 20)
        self.assertEqual(len(c.filter_by_identity()), 20)
        self.assertEqual(len(c.filter_by_axis()), 12)
        self.assertEqual(len(c.filter_by_key()), 20)
        self.assertEqual(len(c.filter_by_data()), 12)
        self.assertEqual(len(c.filter_by_property()), 12)
        self.assertEqual(len(c.filter_by_type()), 20)
        self.assertEqual(len(c.filter_by_method()), 2)
        self.assertEqual(len(c.filter_by_measure()), 1)
        self.assertEqual(len(c.filter_by_ncvar()), 14)
        self.assertEqual(len(c.filter_by_ncdim()), 4)

        self.assertEqual(len(c.filter_by_identity("qwerty")), 0)
        self.assertEqual(len(c.filter_by_key("qwerty")), 0)
        self.assertEqual(len(c.filter_by_type("qwerty")), 0)
        self.assertEqual(len(c.filter_by_method("qwerty")), 0)
        self.assertEqual(len(c.filter_by_measure("qwerty")), 0)
        self.assertEqual(len(c.filter_by_ncvar("qwerty")), 0)
        self.assertEqual(len(c.filter_by_ncdim("qwerty")), 0)
        self.assertEqual(len(c.filter_by_size(-1)), 0)

        self.assertEqual(len(c.filter_by_identity("latitude")), 1)
        self.assertEqual(len(c.filter_by_key("dimensioncoordinate1")), 1)
        self.assertEqual(len(c.filter_by_type("cell_measure")), 1)
        self.assertEqual(len(c.filter_by_method("mean")), 1)
        self.assertEqual(len(c.filter_by_measure("area")), 1)
        self.assertEqual(len(c.filter_by_ncvar("a")), 1)
        self.assertEqual(len(c.filter_by_ncdim("y")), 1)
        self.assertEqual(len(c.filter_by_size(9)), 1)

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

        constructs = c.filter_by_size(9, 10)
        n = 2
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

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

        # Property
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

        # Axis
        for mode in ("and", "or", "exact", "subset"):
            for args in (
                ["qwerty"],
                ["domainaxis0"],
                ["domainaxis0", "domainaxis1"],
                ["domainaxis0", "domainaxis1", "domainaxis2"],
            ):
                d = c.filter_by_axis(mode, *args)
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

    def test_Constructs_copy(self):
        """TODO DOCS."""
        f = cfdm.example_field(1)
        c = f.constructs

        copy.copy(c)
        copy.deepcopy(c)

    def test_Constructs__getitem__(self):
        """TODO DOCS."""
        f = cfdm.example_field(1)
        c = f.constructs

        with self.assertRaises(KeyError):
            c["qwerty"]

        self.assertIsInstance(
            c["auxiliarycoordinate1"], cfdm.AuxiliaryCoordinate
        )

        del c._constructs["auxiliary_coordinate"]
        with self.assertRaises(KeyError):
            c["auxiliarycoordinate1"]

        with self.assertRaises(KeyError):
            c["qwerty"]

    def test_Constructs_private(self):
        """TODO DOCS."""
        f = cfdm.example_field(1)
        c = f.domain.constructs

        # _dictionary
        self.assertIsInstance(c._dictionary(copy=True), dict)

        # _construct_type_description
        self.assertEqual(
            c._construct_type_description("auxiliary_coordinate"),
            "auxiliary coordinate",
        )

        # _check_construct_type
        self.assertIsNone(c._check_construct_type(None))
        self.assertIsNone(c._check_construct_type("cell_method", None))

        x = c.copy()
        del x._constructs["auxiliary_coordinate"]
        with self.assertRaises(KeyError):
            x["auxiliarycoordinate1"]

        with self.assertRaises(KeyError):
            x["qwerty"]

        # _del_construct
        x = f.constructs.copy()

        x._del_construct("domainancillary0")

        with self.assertRaises(ValueError):
            x._del_construct("domainaxis1")

        x._del_construct("dimensioncoordinate3")
        with self.assertRaises(ValueError):
            x._del_construct("domainaxis3")

        x = f.domain.constructs.copy()
        x._del_construct("dimensioncoordinate3")
        self.assertIsInstance(x._del_construct("domainaxis3"), cfdm.DomainAxis)

        # _set_construct
        x = f.constructs.copy()
        with self.assertRaises(ValueError):
            x._set_construct(f.construct("cellmethod0"), axes=["domainaxis0"])

        # _set_construct_data_axes
        x = f.constructs.copy()
        with self.assertRaises(ValueError):
            x._set_construct_data_axes("qwerty", ["domainaxis"])

        with self.assertRaises(ValueError):
            x._set_construct_data_axes("auxiliarycoordinate1", ["qwerty"])

        with self.assertRaises(ValueError):
            x._set_construct_data_axes("auxiliarycoordinate1", ["domainaxis0"])

        # _pop
        x = c.copy()
        with self.assertRaises(KeyError):
            x._pop("qwerty")


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
