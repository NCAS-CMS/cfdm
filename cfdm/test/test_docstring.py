import datetime
import faulthandler
import inspect
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


def _recurse_on_subclasses(klass):
    """Return all unique subclasses of a classes' subclass hierarchy."""
    return set(klass.__subclasses__()).union(
        [
            sub
            for cls in klass.__subclasses__()
            for sub in _recurse_on_subclasses(cls)
        ]
    )


def _get_all_abbrev_subclasses(klass):
    """Return subclasses of the class hierarchy with some filtered out.

    Filter out cf.mixin.properties*.Properties* (by means of there not
    being any abbreviated cf.Properties* classes) plus any cfdm classes,
    since this function needs to take cf subclasses from cfdm classes as
    well.

    """
    return tuple(
        [
            sub
            for sub in _recurse_on_subclasses(klass)
            if hasattr(cfdm, sub.__name__)
        ]
    )


class DocstringTest(unittest.TestCase):
    """Test the system for cross-package docstring substitutions."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        self.package = "cfdm"
        self.repr = ""

        self.subclasses_of_Container = tuple(
            set(
                _get_all_abbrev_subclasses(cfdm.mixin.container.Container)
            ).union(
                set(
                    _get_all_abbrev_subclasses(
                        cfdm.core.abstract.container.Container
                    )
                ),
                set(
                    _get_all_abbrev_subclasses(cfdm.data.abstract.array.Array)
                ),
                [  # other key classes not in subclass heirarchy above
                    cfdm.data.NumpyArray
                ],
            )
        )

        self.subclasses_of_Properties = _get_all_abbrev_subclasses(
            cfdm.mixin.properties.Properties
        )

        self.subclasses_of_PropertiesData = _get_all_abbrev_subclasses(
            cfdm.mixin.propertiesdata.PropertiesData
        )

        self.subclasses_of_PropertiesDataBounds = _get_all_abbrev_subclasses(
            cfdm.mixin.propertiesdatabounds.PropertiesDataBounds
        )

    def test_class_docstring_rewrite(self):
        """Test the DocstringRewriteMeta (meta)class."""

        class parent(metaclass=cfdm.core.meta.DocstringRewriteMeta):
            pass

        class child(parent):
            pass

        class grandchild(child):
            pass

        self.assertIsNone(parent.__doc__)
        self.assertIsNone(child.__doc__)
        self.assertIsNone(grandchild.__doc__)

        class parent(metaclass=cfdm.core.meta.DocstringRewriteMeta):
            """No sub 0."""

        class child(parent):
            pass

        class grandchild(child):
            pass

        self.assertEqual(parent.__doc__, "No sub 0.")
        self.assertIsNone(child.__doc__)
        self.assertIsNone(grandchild.__doc__)

        class parent(metaclass=cfdm.core.meta.DocstringRewriteMeta):
            """{{class}}."""

        class child(parent):
            pass

        class grandchild(child):
            pass

        self.assertEqual(parent.__doc__, "parent.")
        self.assertEqual(child.__doc__, "child.")
        self.assertEqual(grandchild.__doc__, "grandchild.")

        class child(parent):
            """No sub 1."""

        class grandchild(child):
            pass

        class greatgrandchild(grandchild):
            pass

        self.assertEqual(parent.__doc__, "parent.")
        self.assertEqual(child.__doc__, "No sub 1.")
        self.assertIsNone(grandchild.__doc__)
        self.assertIsNone(greatgrandchild.__doc__)

        class greatgrandchild(grandchild):
            """No sub 3."""

        self.assertEqual(parent.__doc__, "parent.")
        self.assertEqual(child.__doc__, "No sub 1.")
        self.assertIsNone(grandchild.__doc__)
        self.assertEqual(greatgrandchild.__doc__, "No sub 3.")

        class grandchild(child):
            """No sub 2."""

        class greatgrandchild(grandchild):
            pass

        self.assertEqual(parent.__doc__, "parent.")
        self.assertEqual(child.__doc__, "No sub 1.")
        self.assertEqual(grandchild.__doc__, "No sub 2.")
        self.assertIsNone(greatgrandchild.__doc__)

        class grandchild(child):
            """Sub 2 {{class}}."""

        class greatgrandchild(grandchild):
            pass

        self.assertEqual(parent.__doc__, "parent.")
        self.assertEqual(child.__doc__, "No sub 1.")
        self.assertEqual(grandchild.__doc__, "Sub 2 grandchild.")
        self.assertEqual(greatgrandchild.__doc__, "Sub 2 greatgrandchild.")

        class parent(metaclass=cfdm.core.meta.DocstringRewriteMeta):
            pass

        class child(parent):
            """{{class}}."""

        class grandchild(child):
            pass

        self.assertIsNone(parent.__doc__)
        self.assertEqual(child.__doc__, "child.")
        self.assertEqual(grandchild.__doc__, "grandchild.")

    def test_docstring(self):
        """Test that all double-brace markers have been substituted."""
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                for name in dir(x):
                    f = getattr(klass, name, None)

                    if f is None or not hasattr(f, "__doc__"):
                        continue

                    if name.startswith("__") and not inspect.isfunction(f):
                        continue

                    self.assertIsNotNone(
                        f.__doc__,
                        f"\n\nCLASS: {klass}\n"
                        f"METHOD NAME: {name}\n"
                        f"METHOD: {f}\n__doc__: {f.__doc__}",
                    )

                    self.assertNotIn(
                        "{{",
                        f.__doc__,
                        f"\n\nCLASS: {klass}\n"
                        f"METHOD NAME: {name}\n"
                        f"METHOD: {f}",
                    )

    def test_docstring_package(self):
        """Test the docstring substitution of the pacakage name."""
        string = f">>> f = {self.package}."
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                self.assertIn(string, x._has_component.__doc__, klass)

        string = f">>> f = {self.package}."
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.clear_properties.__doc__, klass)

    def test_docstring_class(self):
        """Test the docstring substitution of the class name."""
        for klass in self.subclasses_of_Properties:
            string = f">>> f = {self.package}.{klass.__name__}"
            for x in (klass, klass()):
                self.assertIn(
                    string,
                    x.clear_properties.__doc__,
                    f"\n\nCLASS: {klass}\n"
                    "METHOD NAME: clear_properties\n"
                    f"METHOD: {x.clear_properties}",
                )

        for klass in self.subclasses_of_Container:
            string = klass.__name__
            for x in (klass, klass()):
                self.assertIn(string, x.copy.__doc__, klass)

        for klass in self.subclasses_of_PropertiesDataBounds:
            string = f"{klass.__name__}"
            for x in (klass, klass()):
                self.assertIn(
                    string,
                    x.insert_dimension.__doc__,
                    f"\n\nCLASS: {klass}\n"
                    f"METHOD NAME: {klass.__name__}\n"
                    "METHOD: insert_dimension",
                )

    def test_docstring_repr(self):
        """Test docstring substitution of the object representation."""
        string = f"<{self.repr}Data"
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertIn(string, x.has_data.__doc__, klass)

    def test_docstring_default(self):
        """Test a given string gets substituted into a docstring."""
        string = "Return the value of the *default* parameter"
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.del_property.__doc__, klass)

    def test_docstring_staticmethod(self):
        """Test docstring substitution on a static method."""
        for klass in self.subclasses_of_PropertiesData:
            x = klass
            self.assertEqual(
                x._test_docstring_substitution_staticmethod(1, 2), (1, 2)
            )

    def test_docstring_classmethod(self):
        """Test docstring substitution on a class method."""
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertEqual(
                    x._test_docstring_substitution_classmethod(1, 2), (1, 2)
                )

    def test_docstring_docstring_substitutions(self):
        """Test the `_docstring substitution` internal method."""
        for klass in self.subclasses_of_Container:
            for x in (klass,):
                d = x._docstring_substitutions(klass)
                self.assertIsInstance(d, dict)
                self.assertIn("{{repr}}", d)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
