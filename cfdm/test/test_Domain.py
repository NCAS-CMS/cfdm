import datetime
import inspect
import os
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts


import cfdm


class DomainTest(unittest.TestCase):
    """TODO DOCS."""

    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
    )
    f = cfdm.read(filename)[0]
    d = f.domain

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
        self.test_only = []

    def test_Domain__repr__str__dump(self):
        """TODO DOCS."""
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.example_field(1).domain

        # repr
        _ = repr(d)

        # str
        _ = str(d)

        # dump
        self.assertIsInstance(d.dump(display=False), str)

        d.nc_set_variable("domain1")
        for title in (None, "title"):
            _ = d.dump(display=False, _title=title)

        d.nc_del_variable()
        for title in (None, "title"):
            _ = d.dump(display=False, _title=title)

    def test_Domain__init__(self):
        d = cfdm.Domain(source="qwerty")

    def test_Domain_equals(self):
        """TODO DOCS."""
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.example_field(1).domain
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

        e = cfdm.example_field(0).domain
        self.assertFalse(e.equals(d))

        e.set_property("foo", "bar")
        self.assertFalse(e.equals(d))

    def test_Domain_properties(self):
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
        d = cfdm.example_field(1).domain

        self.assertIsInstance(
            d.del_construct("dimensioncoordinate1"), cfdm.DimensionCoordinate
        )

    def test_Domain_climatological_time_axes(self):
        f = cfdm.example_field(7)
        d = f.domain

        self.assertEqual(d.climatological_time_axes(), set())

        cm = cfdm.CellMethod(axes="domainaxis0", method="mean")
        cm.set_qualifier("over", "years")
        f.set_construct(cm)

        self.assertEqual(d.climatological_time_axes(), set(("domainaxis0",)))

    def test_Domain_creation_commands(self):
        d = cfdm.example_field(1).domain

        with self.assertRaises(ValueError):
            x = d.creation_commands(name="c")

        with self.assertRaises(ValueError):
            x = d.creation_commands(name="data", data_name="data")

        d.nc_set_global_attribute("foo", "bar")
        d = d.creation_commands(namespace="my_cfdm", header=True)

    def test_Domain_identity(self):
        d = cfdm.example_field(1).domain

        d.nc_set_variable("qwerty")
        self.assertEqual(d.identity(), "ncvar%qwerty")

        d.set_property("long_name", "qwerty")
        self.assertEqual(d.identity(), "long_name=qwerty")

    def test_Domain_identites(self):
        d = cfdm.example_field(1).domain

        d.nc_set_variable("qwerty")
        d.set_property("cf_role", "qwerty")
        d.set_property("long_name", "qwerty")
        d.set_property("foo", "bar")

        self.assertEqual(
            d.identities(),
            ["cf_role=qwerty", "long_name=qwerty", "foo=bar", "ncvar%qwerty"],
        )

    def test_Domain_apply_masking(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = self.d.copy()

        self.assertIsNone(d.apply_masking(inplace=True))
        self.assertTrue(d.equals(d.apply_masking()))

    def test_Domain_data(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertFalse(self.d.has_data())

    def test_Domain_has_bounds(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertFalse(self.d.has_bounds())


# --- End: class


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
