import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DomainTest(unittest.TestCase):
    """Unit test for the Domain class."""

    f = cfdm.example_field(1)
    d = f.domain

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

    def test_Domain__repr__str__dump(self):
        """Test all means of Domain inspection."""
        d = self.d

        repr(d)
        str(d)
        self.assertIsInstance(d.dump(display=False), str)

        d.nc_set_variable("domain1")
        for title in (None, "title"):
            d.dump(display=False, _title=title)

        d.nc_del_variable()
        for title in (None, "title"):
            d.dump(display=False, _title=title)

        # Test when any construct which can have data in fact has no data.
        d = d.copy()
        for identity in [
            "time",  # a dimension coordinate
            "latitude",  # an auxiliary coordinate
            "measure:area",  # a cell measure
            "surface_altitude",  # a domain ancillary
        ]:
            c = d.construct(identity)  # get relevant construct, type as above
            c.del_data()
            self.assertFalse(c.has_data())
            str(d)
            repr(d)

    def test_Domain__init__(self):
        """Test the Domain constructor and source keyword."""
        cfdm.Domain(source="qwerty")

    def test_Domain_equals(self):
        """Test the equality-testing Domain method."""
        d = self.d
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

        e = cfdm.example_field(0).domain
        self.assertFalse(e.equals(d))

        e.set_property("foo", "bar")
        self.assertFalse(e.equals(d))

    def test_Domain_properties(self):
        """Test the property access methods of Domain."""
        d = cfdm.Domain()

        d.set_property("long_name", "qwerty")

        self.assertEqual(d.properties(), {"long_name": "qwerty"})
        self.assertEqual(d.get_property("long_name"), "qwerty")
        self.assertEqual(d.del_property("long_name"), "qwerty")
        self.assertIsNone(d.get_property("long_name", None))
        self.assertIsNone(d.del_property("long_name", None))

        d.set_property("long_name", "qwerty")
        self.assertEqual(d.clear_properties(), {"long_name": "qwerty"})

        d.set_properties({"long_name": "qwerty"})
        d.set_properties({"foo": "bar"})
        self.assertEqual(d.properties(), {"long_name": "qwerty", "foo": "bar"})

    def test_Domain_del_construct(self):
        """Test the `del_construct` Domain method."""
        d = self.d.copy()

        self.assertIsInstance(
            d.del_construct("dimensioncoordinate1"), cfdm.DimensionCoordinate
        )

    def test_Domain_climatological_time_axes(self):
        """Test the `climatological_time_axes` method of Domain."""
        f = cfdm.example_field(7)
        d = f.domain

        self.assertEqual(d.climatological_time_axes(), set())

        cm = cfdm.CellMethod(axes="domainaxis0", method="mean")
        cm.set_qualifier("over", "years")
        f.set_construct(cm)

        self.assertEqual(d.climatological_time_axes(), set(("domainaxis0",)))

    def test_Domain_creation_commands(self):
        """Test the `creation_commands` Domain method."""
        d = self.d.copy()

        with self.assertRaises(ValueError):
            d.creation_commands(name="c")

        with self.assertRaises(ValueError):
            d.creation_commands(name="data", data_name="data")

        d.nc_set_global_attribute("foo", "bar")
        d = d.creation_commands(namespace="my_cfdm", header=True)

    def test_Domain_identity(self):
        """Test the `identity` Domain method."""
        d = self.d

        d.nc_set_variable("qwerty")
        self.assertEqual(d.identity(), "ncvar%qwerty")

        d.set_property("long_name", "qwerty")
        self.assertEqual(d.identity(), "long_name=qwerty")

    def test_Domain_identites(self):
        """Test the `identities` Domain method."""
        d = self.d.copy()

        d.nc_set_variable("qwerty")
        d.set_property("cf_role", "qwerty")
        d.set_property("long_name", "qwerty")
        d.set_property("foo", "bar")

        self.assertEqual(
            d.identities(),
            ["cf_role=qwerty", "long_name=qwerty", "foo=bar", "ncvar%qwerty"],
        )

    def test_Domain_apply_masking(self):
        """Test the `apply_masking` Domain method."""
        d = self.d.copy()

        self.assertIsNone(d.apply_masking(inplace=True))
        self.assertTrue(d.equals(d.apply_masking()))

    def test_Domain_data(self):
        """Test that Domain instances do not have data."""
        self.assertFalse(self.d.has_data())

    def test_Domain_has_bounds(self):
        """Test that Domain instances do not have cell bounds."""
        self.assertFalse(self.d.has_bounds())

    def test_Domain_get_data_axes(self):
        """Test Domain.get_data_axes."""
        d = cfdm.example_domain(0)
        self.assertEqual(d.get_data_axes("latitude"), ("domainaxis0",))

        with self.assertRaises(ValueError):
            d.get_data_axes(None)

        with self.assertRaises(ValueError):
            d.get_data_axes("domainaxis0")

    def test_Domain_get_original_filenames(self):
        """Test Domain.get_original_filenames."""
        d = cfdm.example_field(0).domain
        self.assertEqual(d.get_original_filenames(), set())

        x = d.coordinate("longitude")
        x._original_filenames(define=["file1.nc", "file3.nc"])
        b = x.bounds
        b._original_filenames(define=["file1.nc", "file4.nc"])

        self.assertEqual(
            d.get_original_filenames(),
            set(
                (
                    cfdm.abspath("file1.nc"),
                    cfdm.abspath("file3.nc"),
                    cfdm.abspath("file4.nc"),
                )
            ),
        )


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
