import atexit
import datetime
import faulthandler
import os
import re
import tempfile
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_Field.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tmpfile,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class FieldTest(unittest.TestCase):
    """Unit test for the Field class."""

    f0 = cfdm.example_field(0)
    f1 = cfdm.example_field(1)

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

    def test_Field__repr__str__dump_construct_type(self):
        """Test all means of Field inspection."""
        f = self.f1

        repr(f)
        str(f)
        self.assertIsInstance(f.dump(display=False), str)
        self.assertIsInstance(f.dump(data=False, display=False), str)
        self.assertEqual(f.construct_type, "field")

        # Test when any construct which can have data in fact has no data.
        f = f.copy()
        for identity in [
            "time",  # a dimension coordinate
            "latitude",  # an auxiliary coordinate
            "measure:area",  # a cell measure
            "surface_altitude",  # a domain ancillary,
            "air_temperature standard_error",  # a field ancillary
        ]:
            c = f.construct(identity)  # get relevant construct, type as above
            c.del_data()
            self.assertFalse(c.has_data())
            str(f)
            repr(f)

    def test_Field__init__(self):
        """Test the Field constructor and source keyword."""
        cfdm.Field(source="qwerty")

    def test_Field__getitem__(self):
        """Test the access of field subspsaces from Field."""
        f = self.f1
        f = f.squeeze()

        d = f.data.array

        g = f[...]
        self.assertTrue((g.data.array == d).all())

        g = f[:, :]
        self.assertTrue((g.data.array == d).all())

        g = f[slice(None), :]
        self.assertTrue((g.data.array == d).all())

        g = f[slice(None), slice(None)]
        self.assertTrue((g.data.array == d).all())

        g = f[slice(None), ...]
        self.assertTrue((g.data.array == d).all())

        g = f[..., slice(None)]
        self.assertTrue((g.data.array == d).all())

        g = f[:, slice(0, f.data.shape[1], 1)]
        self.assertTrue((g.data.array == d).all())

        for indices, shape, multiple_list_indices in (
            [(slice(0, None, 1), slice(0, None)), (10, 9), False],
            [(slice(3, 7), slice(2, 5)), (4, 3), False],
            [(slice(6, 2, -1), slice(4, 1, -1)), (4, 3), False],
            # [(1, 3), ( 1, 1), False],
            # [(-2, -4), ( 1, 1), False],
            # [(-2, slice(1, 5)), ( 1, 4), False],
            # [(slice(5, 1, -2), 7), ( 2, 1), False],
            [([1, 4, 7], slice(1, 5)), (3, 4), False],
            [([1, 4, 7], slice(6, 8)), (3, 2), False],
            [(slice(6, 8), [1, 4, 7]), (2, 3), False],
            [([0, 3, 8], [1, 7, 8]), (3, 3), True],
            [([8, 3, 0], [8, 7, 1]), (3, 3), True],
        ):
            g = f[indices]

            if not multiple_list_indices:
                e = d[indices]
            else:
                e = d.copy()
                indices = list(indices)
                for axis, i in enumerate(indices):
                    if isinstance(i, list):
                        e = np.take(e, indices=i, axis=axis)
                        indices[axis] = slice(None)

                e = e[tuple(indices)]

            self.assertEqual(
                g.data.shape,
                e.data.shape,
                f"Bad shape for {indices}: {g.data.shape} != {e.data.shape}",
            )
            self.assertTrue(
                (g.data.array == e).all(),
                f"Bad values for {indices}: {g.data.array} != {e}",
            )

        # Check slicing of bounds
        g = f[..., 0:4]
        c = g.construct("grid_longitude")
        b = c.bounds
        self.assertEqual(c.data.shape, (4,))
        self.assertEqual(b.data.shape, (4, 2))

        # Indices result in a subspaced shape that has a size 0 axis
        with self.assertRaises(IndexError):
            f[..., [False] * f.shape[-1]]

    def test_Field_get_filenames(self):
        """Test Field.get_filenames."""
        cfdm.write(self.f0, tmpfile)
        f = cfdm.read(tmpfile)[0]

        abspath_tmpfile = os.path.abspath(tmpfile)
        self.assertEqual(f.get_filenames(), set([abspath_tmpfile]))

        f.persist(inplace=True, metadata=True)
        self.assertEqual(f.get_filenames(), set())

    def test_Field_apply_masking(self):
        """Test the `apply_masking` Field method."""
        f = self.f0.copy()

        for prop in (
            "missing_value",
            "_FillValue",
            "valid_min",
            "valid_max",
            "valid_range",
        ):
            f.del_property(prop, None)

        d = f.data.copy()
        g = f.copy()
        self.assertIsNone(f.apply_masking(inplace=True))
        self.assertTrue(f.equals(g, verbose=3))

        x = 0.11
        y = 0.1
        z = 0.2

        f.set_property("_FillValue", x)
        d = f.data.copy()

        g = f.apply_masking()
        e = d.apply_masking(fill_values=[x])
        self.assertTrue(e.equals(g.data, verbose=3))
        self.assertEqual(g.data.array.count(), g.data.size - 1)

        f.set_property("valid_range", [y, z])
        d = f.data.copy()
        g = f.apply_masking()
        e = d.apply_masking(fill_values=[x], valid_range=[y, z])
        self.assertTrue(e.equals(g.data, verbose=3))

        f.del_property("valid_range")
        f.set_property("valid_min", y)
        g = f.apply_masking()
        e = d.apply_masking(fill_values=[x], valid_min=y)
        self.assertTrue(e.equals(g.data, verbose=3))

        f.del_property("valid_min")
        f.set_property("valid_max", z)
        g = f.apply_masking()
        e = d.apply_masking(fill_values=[x], valid_max=z)
        self.assertTrue(e.equals(g.data, verbose=3))

        f.set_property("valid_min", y)
        g = f.apply_masking()
        e = d.apply_masking(fill_values=[x], valid_min=y, valid_max=z)
        self.assertTrue(e.equals(g.data, verbose=3))

    def test_Field_PROPERTIES(self):
        """Test the property access methods of Field."""
        f = self.f1.copy()
        for name, value in f.properties().items():
            self.assertTrue(f.has_property(name))
            f.get_property(name)
            f.del_property(name)
            self.assertIsNone(f.del_property(name, default=None))
            self.assertIsNone(f.get_property(name, default=None))
            self.assertFalse(f.has_property(name))
            f.set_property(name, value)

        d = f.clear_properties()
        self.assertIsInstance(d, dict)

        f.set_properties(d)
        f.set_properties(d, copy=False)

    def test_Field_set_get_del_has_data(self):
        """Test the data access and (un)setting methods of Field."""
        f = self.f1.copy()

        self.assertTrue(f.has_data())
        data = f.get_data()
        self.assertIsInstance(f.del_data(), cfdm.Data)
        self.assertIsNone(f.get_data(default=None))
        self.assertIsNone(f.del_data(default=None))
        self.assertFalse(f.has_data())
        self.assertIsNone(f.set_data(data, axes=None))
        self.assertIsNone(f.set_data(data, axes=None, copy=False))
        self.assertTrue(f.has_data())

        f = self.f1.copy()
        self.assertIsInstance(f.del_data_axes(), tuple)
        self.assertFalse(f.has_data_axes())
        self.assertIsNone(f.del_data_axes(default=None))

        f = self.f1.copy()
        for key in f.constructs.filter_by_data():
            self.assertTrue(f.has_data_axes(key))
            self.assertIsInstance(f.get_data_axes(key), tuple)
            self.assertIsInstance(f.del_data_axes(key), tuple)
            self.assertIsNone(f.del_data_axes(key, default=None))
            self.assertIsNone(f.get_data_axes(key, default=None))
            self.assertFalse(f.has_data_axes(key))

        # Test inplace
        f = self.f1.copy()
        d = f.del_data()
        g = f.set_data(d, inplace=False)
        self.assertIsInstance(g, cfdm.Field)
        self.assertFalse(f.has_data())
        self.assertTrue(g.has_data())
        self.assertTrue(g.data.equals(d))

    def test_Field_construct_item(self):
        """Test the `construct_item` Field method."""
        f = self.f1

        out = f.construct_item("key%domainaxis0")
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], "domainaxis0")
        self.assertIsInstance(out[1], cfdm.DomainAxis)

    def test_Field_CONSTRUCTS(self):
        """Test the construct access Field methods."""
        f = self.f1

        f.construct("latitude")
        self.assertIsNone(f.construct("NOT_latitude", default=None))
        self.assertIsNone(f.construct(re.compile("^l"), default=None))

        key = f.construct_key("latitude")
        f.get_construct(key)
        self.assertIsNone(f.get_construct("qwerty", default=None))

        constructs = f.auxiliary_coordinates()
        n = 3
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.AuxiliaryCoordinate)

        constructs = f.cell_measures()
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMeasure)

        constructs = f.cell_methods()
        n = 2
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMethod)

        # Check that no cell methods are returned when a bad
        # identifier is provided
        self.assertFalse(f.cell_methods("bad identifier"))

        constructs = f.coordinate_references()
        n = 2
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CoordinateReference)

        constructs = f.dimension_coordinates()
        n = 4
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DimensionCoordinate)

        constructs = f.domain_ancillaries()
        n = 3
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = f.field_ancillaries()
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.FieldAncillary)

        constructs = f.domain_topologies()
        n = 0
        self.assertEqual(len(constructs), n)

        constructs = f.cell_connectivities()
        n = 0
        self.assertEqual(len(constructs), n)

        # Domain axis key
        ckey = f.construct_key("grid_latitude")
        dakey = f.get_data_axes(ckey)[0]
        self.assertEqual(f.domain_axis_key("grid_latitude"), dakey)
        self.assertIsNone(f.domain_axis_key("XXXX_latitude", default=None))
        self.assertIsNone(
            f.domain_axis_key(re.compile("^grid_"), default=None)
        )

        # UGRID
        f = cfdm.example_field(8)

        constructs = f.domain_topologies()
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainTopology)

        constructs = f.cell_connectivities()
        n = 1
        self.assertEqual(len(constructs), n)
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellConnectivity)

    def test_Field_domain_axes(self):
        """Test the `domain_axes` Field method."""
        f = self.f1

        regex = re.compile("^atmos")

        self.assertEqual(len(f.domain_axes()), 4)
        self.assertEqual(len(f.domain_axes("grid_latitude", -1)), 2)
        self.assertEqual(len(f.domain_axes(regex)), 1)
        self.assertEqual(len(f.domain_axes(regex, "grid_latitude", -1)), 3)

    def test_Field_data_axes(self):
        """Test the data axes access and (un)setting Field methods."""
        f = self.f1.copy()

        ref = f.get_data_axes()

        self.assertEqual(f.get_data_axes(default=None), ref)

        self.assertEqual(f.del_data_axes(), ref)
        self.assertIsNone(f.del_data_axes(default=None))

        self.assertIsNone(f.set_data_axes(ref))
        self.assertEqual(f.get_data_axes(), ref)

    def test_Field_convert(self):
        """Test the convert Field method."""
        f = self.f1

        key = f.construct_key("grid_latitude")
        c = f.convert(key)

        self.assertEqual(c.data.ndim, 1)
        self.assertEqual(c.get_property("standard_name"), "grid_latitude")
        self.assertEqual(len(c.dimension_coordinates()), 1)
        self.assertEqual(len(c.auxiliary_coordinates()), 1)
        self.assertEqual(len(c.cell_measures()), 0)
        self.assertEqual(len(c.coordinate_references()), 1)
        self.assertEqual(len(c.domain_ancillaries()), 0)
        self.assertEqual(len(c.field_ancillaries()), 0)
        self.assertEqual(len(c.cell_methods()), 0)

        key = f.construct_key("latitude")
        c = f.convert(key)

        self.assertEqual(c.data.ndim, 2)
        self.assertEqual(c.get_property("standard_name"), "latitude")
        self.assertEqual(len(c.dimension_coordinates()), 2)
        self.assertEqual(len(c.auxiliary_coordinates()), 3)
        self.assertEqual(len(c.cell_measures()), 1)
        self.assertEqual(len(c.coordinate_references()), 1)
        self.assertEqual(len(c.domain_ancillaries()), 0)
        self.assertEqual(len(c.field_ancillaries()), 0)
        self.assertEqual(len(c.cell_methods()), 0)

        with self.assertRaises(ValueError):
            f.convert("qwerty")

        # Test some constructs which can never have data
        with self.assertRaises(ValueError):
            f.convert("cellmethod0")
        with self.assertRaises(ValueError):
            f.convert("domainaxis0")

    def test_Field_equals(self):
        """Test the equality-testing Field method."""
        f = self.f1

        self.assertTrue(f.equals(f, verbose=3))

        g = f.copy()
        self.assertTrue(f.equals(g, verbose=3))
        self.assertTrue(g.equals(f, verbose=3))

        g = f[...]
        self.assertTrue(f.equals(g, verbose=3))
        self.assertTrue(g.equals(f, verbose=3))

        g = g.squeeze()
        self.assertFalse(f.equals(g))

        h = f.copy()
        h.data[...] = h.data.array[...] + 1
        self.assertFalse(f.equals(h))

        # Symmetry
        f = cfdm.example_field(2)
        g = f.copy()
        self.assertTrue(f.equals(g))
        self.assertTrue(g.equals(f))

        g.del_construct("dimensioncoordinate0")
        self.assertFalse(f.equals(g))
        self.assertFalse(g.equals(f))

    def test_Field_del_construct(self):
        """Test the `del_construct` Field method."""
        f = self.f1.copy()

        self.assertIsInstance(
            f.del_construct("auxiliarycoordinate1"), cfdm.AuxiliaryCoordinate
        )

        with self.assertRaises(ValueError):
            f.del_construct("auxiliarycoordinate1")

        self.assertIsNone(
            f.del_construct("auxiliarycoordinate1", default=None)
        )

        self.assertIsInstance(
            f.del_construct("measure:area"), cfdm.CellMeasure
        )

    def test_Field_has_construct(self):
        """Test the `has_construct` Field method."""
        f = self.f1.copy()

        self.assertTrue(f.has_construct("latitude"))

        self.assertTrue(f.has_construct("auxiliarycoordinate1"))

        self.assertFalse(f.has_construct("QWERTY"))

        # Test edge case whereby constructs have Falsy values as key names:
        f.set_construct(cfdm.DomainAxis(0), key="")
        self.assertTrue(f.has_construct(""))

    def test_Field_squeeze(self):
        """Test Field.squeeze."""
        f = self.f1

        for axes in (None, "atmosphere_hybrid_height_coordinate"):
            g = f.squeeze(axes)
            self.assertEqual(g.data.shape, f.data.shape[1:])
            self.assertEqual(g.get_data_axes(), f.get_data_axes()[1:])

        self.assertIsNone(g.squeeze(inplace=True))

    def test_Field_transpose(self):
        """Test Field.transpose."""
        f = self.f1

        g = f.transpose()
        self.assertEqual(g.data.shape, f.data.shape[::-1])
        self.assertEqual(g.get_data_axes(), f.get_data_axes()[::-1])

        g = g.transpose(
            [
                "atmosphere_hybrid_height_coordinate",
                "grid_latitude",
                "grid_longitude",
            ]
        )
        self.assertEqual(g.shape, f.shape)
        self.assertEqual(g.get_data_axes(), f.get_data_axes())

    def test_Field_insert_dimension(self):
        """Test cfdm.Field.insert_dimension method."""
        f = self.f1
        g = f.copy()

        key = g.set_construct(cfdm.DomainAxis(1))
        h = g.insert_dimension(axis=key)
        self.assertEqual(h.data.ndim, f.data.ndim + 1)
        self.assertEqual(h.get_data_axes()[1:], f.get_data_axes())

        key = g.set_construct(cfdm.DomainAxis(1))
        h = g.insert_dimension(position=g.data.ndim, axis=key)
        self.assertEqual(h.data.ndim, f.data.ndim + 1)
        self.assertEqual(h.get_data_axes()[:-1], f.get_data_axes())

        self.assertEqual(g.cell_measure().ndim, 2)
        h = g.insert_dimension(None, constructs=True)
        self.assertEqual(h.cell_measure().ndim, 3)

        f = f.squeeze()
        array = f.array
        for i in tuple(range(f.ndim + 1)) + tuple(range(-1, -f.ndim - 2, -1)):
            self.assertEqual(
                f.insert_dimension(None, i).shape,
                np.expand_dims(array, i).shape,
            )

    def test_Field_compress_uncompress(self):
        """Test the compress and uncompress Field methods."""
        contiguous = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "DSG_timeSeries_contiguous.nc",
        )
        indexed = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "DSG_timeSeries_indexed.nc",
        )
        indexed_contiguous = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "DSG_timeSeriesProfile_indexed_contiguous.nc",
        )

        files = (contiguous, indexed, indexed_contiguous)
        methods = ("contiguous", "indexed", "indexed_contiguous")

        for filename, method in zip(files, methods):
            message = "method=" + method
            for f in cfdm.read(filename):
                self.assertTrue(bool(f.data.get_compression_type()), message)

                u = f.uncompress()
                self.assertFalse(bool(u.data.get_compression_type()), message)
                self.assertTrue(f.equals(u, verbose=3), message)

                for method1 in methods:
                    message += ", method1=" + method1
                    if method1 == "indexed_contiguous":
                        if f.data.ndim != 3:
                            continue
                    elif f.data.ndim != 2:
                        continue

                    c = u.compress(method1)

                    self.assertTrue(
                        bool(c.data.get_compression_type()), message
                    )

                    self.assertTrue(u.equals(c, verbose=3), message)
                    self.assertTrue(f.equals(c, verbose=3), message)

                    c = f.compress(method1)
                    self.assertTrue(
                        bool(c.data.get_compression_type()), message
                    )

                    self.assertTrue(u.equals(c, verbose=3), message)
                    self.assertTrue(f.equals(c, verbose=3), message)

                    cfdm.write(c, tmpfile)
                    c = cfdm.read(tmpfile)[0]

                    self.assertTrue(
                        bool(c.data.get_compression_type()), message
                    )
                    self.assertTrue(f.equals(c, verbose=3), message)

    def test_Field_creation_commands(self):
        """Test the Field.creation_commands."""
        for i in range(12):
            f = cfdm.example_field(i)

        f = self.f1

        for rd in (False, True):
            f.creation_commands(representative_data=rd)

        for indent in (0, 4):
            f.creation_commands(indent=indent)

        for s in (False, True):
            f.creation_commands(string=s)

        for ns in ("cfdm", ""):
            f.creation_commands(namespace=ns)

    def test_Field_has_geometry(self):
        """Test Field.has_geometry."""
        f = self.f1
        self.assertFalse(f.has_geometry())

        f = cfdm.example_field(6)
        self.assertTrue(f.has_geometry())

    def test_Field_climatological_time_axes(self):
        """Test the `climatological_time_axes` method of Field."""
        f = self.f0.copy()
        self.assertEqual(f.climatological_time_axes(), set())

        f.set_construct(
            cfdm.CellMethod("domainaxis2", "mean", {"within": "years"})
        )
        f.set_construct(
            cfdm.CellMethod("domainaxis2", "mean", {"over": "years"})
        )

        cta = f.climatological_time_axes()
        self.assertEqual(cta, set(["domainaxis2"]))

        d = f.get_domain()
        self.assertEqual(d.climatological_time_axes(), cta)

    def test_Field_bounds(self):
        """Test that Field instances do not have cell bounds."""
        f = self.f0
        self.assertFalse(f.has_bounds())

    def test_Field_auxiliary_coordinate(self):
        """Test Field.auxiliary_coordinate."""
        f = self.f1

        for identity in ("auxiliarycoordinate1", "latitude"):
            key, c = f.construct(identity, item=True)
            self.assertTrue(f.auxiliary_coordinate(identity).equals(c))
            self.assertEqual(f.auxiliary_coordinate(identity, key=True), key)

        with self.assertRaises(ValueError):
            f.auxiliary_coordinate("long_name:qwerty")

    def test_Field_coordinate(self):
        """Test Field.coordinate."""
        f = self.f1

        for identity in (
            "latitude",
            "grid_longitude",
            "auxiliarycoordinate1",
            "dimensioncoordinate1",
        ):
            key, c = f.construct(identity, item=True)

        with self.assertRaises(ValueError):
            f.coordinate("long_name:qweRty")

    def test_Field_coordinate_reference(self):
        """Test Field.coordinate_reference."""
        f = self.f1

        for identity in (
            "coordinatereference1",
            "key%coordinatereference0",
            "standard_name:atmosphere_hybrid_height_coordinate",
            "grid_mapping_name:rotated_latitude_longitude",
        ):
            key, c = f.construct(identity, item=True)
            self.assertTrue(f.coordinate_reference(identity).equals(c))
            self.assertEqual(f.coordinate_reference(identity, key=True), key)

        with self.assertRaises(ValueError):
            f.coordinate_reference("qwerty")

    def test_Field_dimension_coordinate(self):
        """Test Field.dimension_coordinate."""
        f = self.f1

        for identity in ("grid_latitude", "dimensioncoordinate1"):
            if identity == "X":
                key, c = f.construct("grid_longitude", item=True)
            else:
                key, c = f.construct(identity, item=True)

            self.assertTrue(f.dimension_coordinate(identity).equals(c))
            self.assertEqual(f.dimension_coordinate(identity, key=True), key)

            k, v = f.dimension_coordinate(identity, item=True)
            self.assertEqual(k, key)
            self.assertTrue(v.equals(c))

        self.assertIsNone(
            f.dimension_coordinate("long_name=qwerty:asd", default=None)
        )
        self.assertEqual(
            len(f.dimension_coordinates("long_name=qwerty:asd")), 0
        )

        with self.assertRaises(ValueError):
            f.dimension_coordinate("long_name:qwerty")

    def test_Field_cell_measure(self):
        """Test Field.cell_measure."""
        f = self.f1

        for identity in ("measure:area", "cellmeasure0"):
            key, c = f.construct(identity, item=True)

            self.assertTrue(f.cell_measure(identity).equals(c))
            self.assertEqual(f.cell_measure(identity, key=True), key)

            self.assertTrue(f.cell_measure(identity).equals(c))
            self.assertEqual(f.cell_measure(identity, key=True), key)

        self.assertEqual(len(f.cell_measures()), 1)
        self.assertEqual(len(f.cell_measures("measure:area")), 1)
        self.assertEqual(len(f.cell_measures(*["measure:area"])), 1)

        self.assertIsNone(f.cell_measure("long_name=qwerty:asd", default=None))
        self.assertEqual(len(f.cell_measures("long_name=qwerty:asd")), 0)

        with self.assertRaises(ValueError):
            f.cell_measure("long_name:qwerty")

    def test_Field_cell_method(self):
        """Test Field.cell_method."""
        f = self.f1

        for identity in ("method:mean", "cellmethod0"):
            key, c = f.construct(identity, item=True)
            self.assertTrue(f.cell_method(identity).equals(c))
            self.assertEqual(f.cell_method(identity, key=True), key)

    def test_Field_domain_ancillary(self):
        """Test Field.domain_ancillary."""
        f = self.f1

        for identity in ("surface_altitude", "domainancillary0"):
            key, c = f.construct(identity, item=True)
            self.assertTrue(f.domain_ancillary(identity).equals(c))
            self.assertEqual(f.domain_ancillary(identity, key=True), key)

        with self.assertRaises(ValueError):
            f.domain_ancillary("long_name:qwerty")

    def test_Field_field_ancillary(self):
        """Test Field.field_ancillary."""
        f = self.f1

        for identity in ("air_temperature standard_error", "fieldancillary0"):
            key, c = f.construct_item(identity)
            self.assertTrue(f.field_ancillary(identity).equals(c))
            self.assertEqual(f.field_ancillary(identity, key=True), key)

        with self.assertRaises(ValueError):
            f.field_ancillary("long_name:qwerty")

    def test_Field_domain_axis(self):
        """Test Field.domain_axis."""
        f = self.f1

        f.domain_axis(1)
        f.domain_axis("domainaxis2")

        with self.assertRaises(ValueError):
            f.domain_axis(99)

        with self.assertRaises(ValueError):
            f.domain_axis("qwerty")

    def test_Field_indices(self):
        """Test Field.indices."""
        f = self.f0

        g = f[f.indices(longitude=112.5)]
        self.assertEqual(g.shape, (5, 1))
        x = g.dimension_coordinate("longitude").data.array
        self.assertTrue((x == 112.5).all())

        g = f[f.indices(longitude=112.5, latitude=[-45, 75])]
        self.assertEqual(g.shape, (2, 1))
        x = g.dimension_coordinate("longitude").data.array
        y = g.dimension_coordinate("latitude").data.array
        self.assertTrue((x == 112.5).all())
        self.assertTrue((y == [-45, 75]).all())

        g = f[f.indices(time=31)]
        self.assertTrue(g.equals(f))

        g = f[f.indices(time=np.array([31, 9999]))]
        self.assertTrue(g.equals(f))

        with self.assertRaises(ValueError):
            f.indices(bad_name=23)

        with self.assertRaises(ValueError):
            f.indices(longitude=-999)

        with self.assertRaises(ValueError):
            f.indices(longitude="bad_value_type")

        # Test for same axis specified twice
        key = f.construct("longitude", key=True)
        with self.assertRaises(ValueError):
            f.indices(**{"longitude": 112.5, key: 22.5})

    def test_Field_get_original_filenames(self):
        """Test Field.orignal_filenames."""
        f = self.f0
        f._original_filenames(define=["file1.nc", "file2.nc"])
        x = f.coordinate("longitude")
        x._original_filenames(define=["file1.nc", "file3.nc"])
        b = x.bounds
        b._original_filenames(define=["file1.nc", "file4.nc"])

        self.assertEqual(
            f.get_original_filenames(),
            set(
                (
                    cfdm.abspath("file1.nc"),
                    cfdm.abspath("file2.nc"),
                    cfdm.abspath("file3.nc"),
                    cfdm.abspath("file4.nc"),
                )
            ),
        )

        self.assertEqual(
            f.get_original_filenames(), f.copy().get_original_filenames()
        )

    def test_Field_del_properties(self):
        """Test the del_properties method of Field."""
        f = cfdm.Field()
        f.set_properties({"project": "CMIP7", "comment": "model"})
        properties = f.properties()

        removed_properties = f.del_properties("project")
        self.assertEqual(removed_properties, {"project": "CMIP7"})
        self.assertEqual(f.properties(), {"comment": "model"})
        f.set_properties(removed_properties)
        self.assertEqual(f.properties(), properties)
        self.assertEqual(f.del_properties("foo"), {})
        self.assertEqual(f.properties(), properties)

        removed_properties = f.del_properties(["project", "comment"])
        self.assertEqual(removed_properties, properties)
        self.assertEqual(f.properties(), {})

    def test_Field_dataset_chunksizes(self):
        """Test the dataset chunk size methods of a Field."""
        f = self.f0.copy()

        f.nc_set_dataset_chunksizes({"latitude": 1})
        self.assertEqual(f.nc_dataset_chunksizes(), (1, 8))
        f.nc_set_dataset_chunksizes({"longitude": 7})
        self.assertEqual(f.nc_dataset_chunksizes(), (1, 7))
        f.nc_set_dataset_chunksizes({"latitude": 4, "longitude": 2})
        self.assertEqual(f.nc_dataset_chunksizes(), (4, 2))
        f.nc_set_dataset_chunksizes([1, 7])
        self.assertEqual(f.nc_dataset_chunksizes(), (1, 7))
        f.nc_set_dataset_chunksizes("contiguous")
        self.assertEqual(f.nc_dataset_chunksizes(), "contiguous")
        f.nc_set_dataset_chunksizes(None)
        self.assertIsNone(f.nc_dataset_chunksizes())

        for c in (64, "64 B"):
            f.nc_set_dataset_chunksizes(c)
            self.assertEqual(f.nc_dataset_chunksizes(), 64)

        f.nc_set_dataset_chunksizes({"latitude": 999}, clip=True)
        self.assertEqual(f.nc_dataset_chunksizes(), (5, 8))

        f.nc_set_dataset_chunksizes({"latitude": 4, "time": 1})
        self.assertEqual(f.nc_dataset_chunksizes(), (4, 8))
        for coord in ("time", "latitude", "longitude"):
            self.assertIsNone(
                f.dimension_coordinate(coord).nc_dataset_chunksizes()
            )

        # todict
        f.nc_set_dataset_chunksizes([3, 4])
        self.assertEqual(
            f.nc_dataset_chunksizes(todict=True),
            {"time": 1, "latitude": 3, "longitude": 4},
        )

        for chunksizes in (None, "contiguous", 1024):
            f.nc_set_dataset_chunksizes(chunksizes)
            with self.assertRaises(ValueError):
                f.nc_dataset_chunksizes(todict=True)

        # ignore keyword
        f.nc_clear_dataset_chunksizes()
        f.nc_set_dataset_chunksizes(
            {"latitude": 4, "BAD_axis": 99}, ignore=True
        )
        self.assertEqual(f.nc_dataset_chunksizes(), (4, 8))
        with self.assertRaises(ValueError):
            f.nc_set_dataset_chunksizes({"latitude": 4, "BAD_axis": 99})

        # filter_kwargs keyword
        f.nc_set_dataset_chunksizes({"latitude": 4}, filter_by_naxes=(1,))
        self.assertEqual(f.nc_dataset_chunksizes(), (4, 8))

        # constructs keyword
        f.nc_set_dataset_chunksizes(
            {"latitude": 4, "time": 1}, constructs=True
        )
        self.assertEqual(f.nc_dataset_chunksizes(), (4, 8))

        f.nc_set_dataset_chunksizes(
            {"latitude": 4, "time": 1}, constructs=True
        )
        self.assertEqual(
            f.dimension_coordinate("time").nc_dataset_chunksizes(), (1,)
        )
        self.assertEqual(
            f.dimension_coordinate("latitude").nc_dataset_chunksizes(), (4,)
        )
        self.assertEqual(
            f.dimension_coordinate("longitude").nc_dataset_chunksizes(), (8,)
        )

        f.nc_set_dataset_chunksizes(
            "contiguous", constructs={"filter_by_axis": ("longitude",)}
        )
        self.assertEqual(f.nc_dataset_chunksizes(), "contiguous")
        self.assertEqual(
            f.dimension_coordinate("time").nc_dataset_chunksizes(), (1,)
        )
        self.assertEqual(
            f.dimension_coordinate("latitude").nc_dataset_chunksizes(), (4,)
        )
        self.assertEqual(
            f.dimension_coordinate("longitude").nc_dataset_chunksizes(),
            "contiguous",
        )

        # clear
        f.nc_set_dataset_chunksizes("contiguous", constructs=True)
        self.assertEqual(f.nc_clear_dataset_chunksizes(), "contiguous")
        self.assertIsNone(
            f.nc_clear_dataset_chunksizes(
                constructs={"filter_by_identity": ("longitude",)}
            )
        )
        self.assertEqual(
            f.dimension_coordinate("latitude").nc_dataset_chunksizes(),
            "contiguous",
        )
        self.assertIsNone(
            f.dimension_coordinate("longitude").nc_dataset_chunksizes()
        )

        f.nc_clear_dataset_chunksizes(constructs={})
        self.assertIsNone(
            f.dimension_coordinate("latitude").nc_dataset_chunksizes()
        )

    def test_Field_concatenate(self):
        """Test Field.concatenate."""
        f = self.f1.copy()

        g = cfdm.Field.concatenate([f.copy()], axis=0)
        self.assertEqual(g.shape, (1, 10, 9))

        x = [f.copy() for i in range(8)]

        g = cfdm.Field.concatenate(x, axis=0)
        self.assertEqual(g.shape, (8, 10, 9))

        key = x[3].construct_key("latitude")
        x[3].del_construct(key)
        g = cfdm.Field.concatenate(x, axis=0)
        self.assertEqual(g.shape, (8, 10, 9))

        with self.assertRaises(Exception):
            g = cfdm.Field.concatenate([], axis=0)

    def test_Field_persist(self):
        """Test Field.persist."""
        f = self.f0.copy()
        cfdm.write(f, tmpfile)
        f = cfdm.read(tmpfile)[0]

        for d in (f.data.todict(), f.coordinate("longitude").data.todict()):
            on_disk = False
            for v in d.values():
                if isinstance(v, cfdm.data.abstract.FileArray):
                    on_disk = True

            self.assertTrue(on_disk)

        g = f.persist()
        d = g.data.todict()
        in_memory = False
        for v in d.values():
            if isinstance(v, np.ndarray):
                in_memory = True

        self.assertTrue(in_memory)

        d = g.coordinate("longitude").data.todict()
        on_disk = False
        for v in d.values():
            if isinstance(v, cfdm.data.abstract.FileArray):
                on_disk = True

        self.assertTrue(on_disk)

        # In-place and metdata
        f = cfdm.read(tmpfile)[0]
        self.assertIsNone(f.persist(metadata=True, inplace=True))
        for d in (
            f.data.todict(),
            f.coordinate("longitude").data.todict(),
        ):
            in_memory = False
            for v in d.values():
                if isinstance(v, np.ndarray):
                    in_memory = True

            self.assertTrue(in_memory)

    def test_Field_unsqueeze(self):
        """Test Field.unsqueeze."""
        f = self.f0.copy()
        self.assertEqual(f.shape, (5, 8))
        g = f.unsqueeze()
        self.assertEqual(g.shape, (1, 5, 8))
        self.assertIsNone(g.unsqueeze(inplace=True))
        self.assertEqual(g.shape, (1, 5, 8))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
