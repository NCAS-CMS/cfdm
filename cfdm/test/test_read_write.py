import atexit
import datetime
import faulthandler
import os
import platform
import subprocess
import tempfile
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

warnings = False

# Set up temporary files
n_tmpfiles = 9
tmpfiles = [
    tempfile.mkstemp("_test_read_write.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tmpfile,
    tmpfileh,
    tmpfileh2,
    tmpfileh3,
    tmpfilec,
    tmpfilec2,
    tmpfilec3,
    tmpfile0,
    tmpfile1,
) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class read_writeTest(unittest.TestCase):
    """Test the reading and writing of field constructs from/to disk."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows: cfdm.LOG_LEVEL('DEBUG')
        #
        # < ... test code ... >
        # cfdm.log_level('DISABLE')
        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

        self.string_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "string_char.nc"
        )

        self.netcdf3_fmts = [
            "NETCDF3_CLASSIC",
            "NETCDF3_64BIT",
            "NETCDF3_64BIT_OFFSET",
            "NETCDF3_64BIT_DATA",
        ]
        self.netcdf4_fmts = [
            "NETCDF4",
            "NETCDF4_CLASSIC",
        ]
        self.netcdf_fmts = self.netcdf3_fmts + self.netcdf4_fmts

    def test_write_filename(self):
        """Test the writing of a named netCDF file."""
        f = cfdm.example_field(0)
        a = f.data.array

        cfdm.write(f, tmpfile)
        g = cfdm.read(tmpfile)

        with self.assertRaises(Exception):
            cfdm.write(g, tmpfile)

        self.assertTrue((a == g[0].data.array).all())

    def test_read_field(self):
        """Test the `extra` keyword argument of the `read` function."""
        # Test field keyword of cfdm.read
        filename = self.filename

        f = cfdm.read(filename)
        self.assertEqual(len(f), 1, "\n" + str(f))

        f = cfdm.read(
            filename, extra=["dimension_coordinate"], warnings=warnings
        )
        self.assertEqual(len(f), 4, "\n" + str(f))

        f = cfdm.read(
            filename, extra=["auxiliary_coordinate"], warnings=warnings
        )
        self.assertEqual(len(f), 4, "\n" + str(f))

        f = cfdm.read(filename, extra="cell_measure")
        self.assertEqual(len(f), 2, "\n" + str(f))

        f = cfdm.read(filename, extra=["field_ancillary"])
        self.assertEqual(len(f), 4, "\n" + str(f))

        f = cfdm.read(filename, extra="domain_ancillary", warnings=warnings)
        self.assertEqual(len(f), 4, "\n" + str(f))

        f = cfdm.read(
            filename,
            extra=["field_ancillary", "auxiliary_coordinate"],
            warnings=warnings,
        )
        self.assertEqual(len(f), 7, "\n" + str(f))

        self.assertEqual(
            len(
                cfdm.read(
                    filename,
                    extra=["domain_ancillary", "auxiliary_coordinate"],
                    warnings=warnings,
                )
            ),
            7,
        )
        self.assertEqual(
            len(
                cfdm.read(
                    filename,
                    extra=[
                        "domain_ancillary",
                        "cell_measure",
                        "auxiliary_coordinate",
                    ],
                    warnings=warnings,
                )
            ),
            8,
        )

        f = cfdm.read(
            filename,
            extra=(
                "field_ancillary",
                "dimension_coordinate",
                "cell_measure",
                "auxiliary_coordinate",
                "domain_ancillary",
            ),
            warnings=warnings,
        )
        self.assertEqual(len(f), 14, "\n" + str(f))

    def test_read_write_format(self):
        """Test the `fmt` keyword argument of the `read` function."""
        f = cfdm.read(self.filename)[0]
        for fmt in self.netcdf_fmts:
            cfdm.write(f, tmpfile, fmt=fmt)
            g = cfdm.read(tmpfile)
            self.assertEqual(len(g), 1)
            g = g[0]
            self.assertTrue(
                f.equals(g, verbose=3), f"Bad read/write of format: {fmt}"
            )

    def test_write_netcdf_mode(self):
        """Test the `mode` parameter to `write`, notably append mode."""
        g = cfdm.read(self.filename)  # note 'g' has one field

        # Test special case #1: attempt to append fields with groups
        # (other than 'root') which should be forbidden. Using fmt="NETCDF4"
        # since it is the only format where groups are allowed.
        #
        # Note: this is not the most natural test to do first, but putting
        # it before the rest reduces spurious seg faults for me, so...
        g[0].nc_set_variable_groups(["forecast", "model"])
        cfdm.write(g, tmpfile, fmt="NETCDF4", mode="w")  # 1. overwrite to wipe
        f = cfdm.read(tmpfile)
        with self.assertRaises(ValueError):
            cfdm.write(g[0], tmpfile, fmt="NETCDF4", mode="a")

        # Test special case #2: attempt to append fields with contradictory
        # featureType to the original file:
        g[0].nc_clear_variable_groups()
        g[0].nc_set_global_attribute("featureType", "profile")
        cfdm.write(
            g,
            tmpfile,
            fmt="NETCDF4",
            mode="w",
            global_attributes=("featureType", "profile"),
        )  # 1. overwrite to wipe
        h = cfdm.example_field(3)
        h.nc_set_global_attribute("featureType", "timeSeries")
        with self.assertRaises(ValueError):
            cfdm.write(h, tmpfile, fmt="NETCDF4", mode="a")
        # Now remove featureType attribute for subsquent tests:
        g_attrs = g[0].nc_clear_global_attributes()
        del g_attrs["featureType"]
        g[0].nc_set_global_attributes(g_attrs)

        # Set a non-trivial (i.e. not only 'Conventions') global attribute to
        # make the global attribute testing more robust:
        add_global_attr = ["remark", "A global comment."]
        original_global_attrs = g[0].nc_global_attributes()
        original_global_attrs[add_global_attr[0]] = None  # -> None on fields
        g[0].nc_set_global_attribute(*add_global_attr)

        # First test a bad mode value:
        with self.assertRaises(ValueError):
            cfdm.write(g[0], tmpfile, mode="g")

        g_copy = g.copy()

        for fmt in self.netcdf_fmts:  # test over all netCDF 3 and 4 formats
            # Other tests cover write as default mode (i.e. test with no mode
            # argument); here test explicit provision of 'w' as argument:
            cfdm.write(
                g,
                tmpfile,
                fmt=fmt,
                mode="w",
                global_attributes=add_global_attr,
            )
            f = cfdm.read(tmpfile)

            new_length = 1  # since 1 == len(g)
            self.assertEqual(len(f), new_length)
            # Ignore as 'remark' should be 'None' on the field as tested below
            self.assertTrue(f[0].equals(g[0], ignore_properties=["remark"]))
            self.assertEqual(
                f[0].nc_global_attributes(), original_global_attrs
            )

            # Main aspect of this test: testing the append mode ('a'): now
            # append all other example fields, to check a diverse variety.
            for ex_field_n, ex_field in enumerate(cfdm.example_fields()):
                # Note: after Issue #141, this skip can be removed.
                if ex_field_n == 1:
                    continue

                # Skip since "RuntimeError: Can't create variable in
                # NETCDF4_CLASSIC file from (2)  (NetCDF: Attempting netcdf-4
                # operation on strict nc3 netcdf-4 file)" i.e. not possible.
                if fmt == "NETCDF4_CLASSIC" and ex_field_n in (6, 7):
                    continue

                # Skip since "Can't write int64 data from <Count: (2) > to a
                # NETCDF3_CLASSIC file" causes a ValueError i.e. not possible.
                # Note: can remove this when Issue #140 is closed.
                if fmt in self.netcdf3_fmts and ex_field_n == 6:
                    continue

                cfdm.write(ex_field, tmpfile, fmt=fmt, mode="a")
                f = cfdm.read(tmpfile)

                new_length += 1  # there should be exactly one more field now
                self.assertEqual(len(f), new_length)
                # Can't guarantee order of fields read in after the appends, so
                # check that the field is *somewhere* in the read-in fieldlist
                self.assertTrue(
                    any(
                        [
                            ex_field.equals(
                                file_field,
                                ignore_properties=[
                                    "comment",
                                    "featureType",
                                    "remark",
                                ],
                            )
                            for file_field in f
                        ]
                    )
                )
                for file_field in f:
                    self.assertEqual(
                        file_field.nc_global_attributes(),
                        original_global_attrs,
                    )

            # Now do the same test, but appending all of the example fields in
            # one operation rather than one at a time, to check that it works.
            cfdm.write(g, tmpfile, fmt=fmt, mode="w")  # 1. overwrite to wipe
            append_ex_fields = cfdm.example_fields()
            del append_ex_fields[1]  # note: can remove after Issue #141 closed
            # Note: can remove this del when Issue #140 is closed:
            if fmt in self.netcdf3_fmts:
                del append_ex_fields[5]  # n=6 ex_field, minus 1 for above del
            if fmt in "NETCDF4_CLASSIC":
                # Remove n=5, 6, 7 for reasons as given above (del => minus 1)
                append_ex_fields = append_ex_fields[:4]

            overall_length = len(append_ex_fields) + 1  # 1 for original 'g'
            cfdm.write(
                append_ex_fields, tmpfile, fmt=fmt, mode="a"
            )  # 2. now append
            f = cfdm.read(tmpfile)
            self.assertEqual(len(f), overall_length)

            # Also test the mode="r+" alias for mode="a".
            cfdm.write(g, tmpfile, fmt=fmt, mode="w")  # 1. overwrite to wipe
            cfdm.write(
                append_ex_fields, tmpfile, fmt=fmt, mode="r+"
            )  # 2. now append
            f = cfdm.read(tmpfile)
            self.assertEqual(len(f), overall_length)

            # The appended fields themselves are now known to be correct,
            # but we also need to check that any coordinates that are
            # equal across different fields have been shared in the
            # source netCDF, rather than written in separately.
            #
            # Note that the coordinates that are shared across the set of
            # all example fields plus the field 'g' from the contents of
            # the original file (self.filename) are as follows:
            #
            # 1. Example fields n=0 and n=1 share:
            #    <DimensionCoordinate: time(1) days since 2018-12-01 >
            # 2. Example fields n=0, n=2 and n=5 share:
            #    <DimensionCoordinate: latitude(5) degrees_north> and
            #    <DimensionCoordinate: longitude(8) degrees_east>
            # 3. Example fields n=2 and n=5 share:
            #    <DimensionCoordinate: air_pressure(1) hPa>
            # 4. The original file field ('g') and example field n=1 share:
            #    <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
            #    <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
            #    <Dimension...: atmosphere_hybrid_height_coordinate(1) >,
            #    <DimensionCoordinate: grid_latitude(10) degrees>,
            #    <DimensionCoordinate: grid_longitude(9) degrees> and
            #    <DimensionCoordinate: time(1) days since 2018-12-01 >
            #
            # Therefore we check all of those coordinates for singularity,
            # i.e. the same underlying netCDF variables, in turn.

            # But first, since the order of the fields appended isn't
            # guaranteed, we must find the mapping of the example fields to
            # their position in the read-in FieldList.
            f = cfdm.read(tmpfile)
            # Element at index N gives position of example field n=N in file
            file_field_order = []
            for ex_field in cfdm.example_fields():
                position = [
                    f.index(file_field)
                    for file_field in f
                    if ex_field.equals(
                        file_field,
                        ignore_properties=["comment", "featureType", "remark"],
                    )
                ]
                if not position:
                    position = [None]  # to record skipped example fields
                file_field_order.append(position[0])

            equal_coors = {
                ((0, "dimensioncoordinate2"), (1, "dimensioncoordinate3")),
                ((0, "dimensioncoordinate0"), (2, "dimensioncoordinate1")),
                ((0, "dimensioncoordinate1"), (2, "dimensioncoordinate2")),
                ((0, "dimensioncoordinate0"), (5, "dimensioncoordinate1")),
                ((0, "dimensioncoordinate1"), (5, "dimensioncoordinate2")),
                ((2, "dimensioncoordinate3"), (5, "dimensioncoordinate3")),
            }
            for coor_1, coor_2 in equal_coors:
                ex_field_1_position, c_1 = coor_1
                ex_field_2_position, c_2 = coor_2
                # Now map the appropriate example field to the file FieldList
                f_1 = file_field_order[ex_field_1_position]
                f_2 = file_field_order[ex_field_2_position]
                # None for fields skipped in test, distinguish from falsy 0
                if f_1 is None or f_2 is None:
                    continue
                self.assertEqual(
                    f[f_1]
                    .constructs()
                    .filter_by_identity(c_1)
                    .value()
                    .nc_get_variable(),
                    f[f_2]
                    .constructs()
                    .filter_by_identity(c_2)
                    .value()
                    .nc_get_variable(),
                )

            # Note: after Issue #141, the block below should be un-commented.
            #
            # The original file field 'g' must be at the remaining position:
            # rem_position = list(set(
            #     range(len(f))).difference(set(file_field_order)))[0]
            # # In the final cases, it is easier to remove the one differing
            # # coordinate to get the equal coordinates that should be shared:
            # original_field_coors = dict(f[rem_position].coordinates())
            # ex_field_1_coors = dict(f[file_field_order[1]].coordinates())
            # for orig_coor, ex_1_coor in zip(
            #         original_field_coors.values(), ex_field_1_coors.values()):
            #     # The 'auxiliarycoordinate2' construct differs for both, so
            #     # skip that but otherwise the two fields have the same coors:
            #     if orig_coor.identity == "auxiliarycoordinate2":
            #         continue
            #     self.assertEqual(
            #         orig_coor.nc_get_variable(),
            #         ex_1_coor.nc_get_variable(),
            #     )

            # Check behaviour when append identical fields, as an edge case:
            cfdm.write(g, tmpfile, fmt=fmt, mode="w")  # 1. overwrite to wipe
            cfdm.write(g_copy, tmpfile, fmt=fmt, mode="a")  # 2. now append
            f = cfdm.read(tmpfile)
            self.assertEqual(len(f), 2 * len(g))
            self.assertTrue(
                any(
                    [
                        file_field.equals(g[0], ignore_properties=["remark"])
                        for file_field in f
                    ]
                )
            )
            self.assertEqual(
                f[0].nc_global_attributes(), original_global_attrs
            )

    def test_read_write_netCDF4_compress_shuffle(self):
        """Test the `compress` and `shuffle` parameters to `write`."""
        f = cfdm.read(self.filename)[0]
        for fmt in self.netcdf4_fmts:
            for shuffle in (True,):
                for compress in (4,):  # range(10):
                    cfdm.write(
                        f, tmpfile, fmt=fmt, compress=compress, shuffle=shuffle
                    )
                    g = cfdm.read(tmpfile)[0]
                    self.assertTrue(
                        f.equals(g, verbose=3),
                        "Bad read/write with lossless compression: "
                        f"{fmt}, {compress}, {shuffle}",
                    )

    def test_read_write_missing_data(self):
        """Test reading and writing of netCDF with missing data."""
        f = cfdm.read(self.filename)[0]
        for fmt in self.netcdf_fmts:
            cfdm.write(f, tmpfile, fmt=fmt)
            g = cfdm.read(tmpfile)[0]
            self.assertTrue(
                f.equals(g, verbose=3), f"Bad read/write of format: {fmt}"
            )

    def test_read_mask(self):
        """Test reading and writing of netCDF with masked data."""
        f = cfdm.example_field(0)

        N = f.size

        f.data[1, 1] = cfdm.masked
        f.data[2, 2] = cfdm.masked

        f.del_property("_FillValue", None)
        f.del_property("missing_value", None)

        cfdm.write(f, tmpfile)

        g = cfdm.read(tmpfile)[0]
        self.assertEqual(numpy.ma.count(g.data.array), N - 2)

        g = cfdm.read(tmpfile, mask=False)[0]
        self.assertEqual(numpy.ma.count(g.data.array), N)

        g.apply_masking(inplace=True)
        self.assertEqual(numpy.ma.count(g.data.array), N - 2)

        f.set_property("_FillValue", 999)
        f.set_property("missing_value", -111)
        cfdm.write(f, tmpfile)

        g = cfdm.read(tmpfile)[0]
        self.assertEqual(numpy.ma.count(g.data.array), N - 2)

        g = cfdm.read(tmpfile, mask=False)[0]
        self.assertEqual(numpy.ma.count(g.data.array), N)

        g.apply_masking(inplace=True)
        self.assertEqual(numpy.ma.count(g.data.array), N - 2)

    def test_write_datatype(self):
        """Test the `datatype` keyword argument to `write`."""
        f = cfdm.read(self.filename)[0]
        self.assertEqual(f.data.dtype, numpy.dtype(float))

        f.set_property("_FillValue", numpy.float64(-999.0))
        f.set_property("missing_value", numpy.float64(-999.0))

        cfdm.write(
            f,
            tmpfile,
            fmt="NETCDF4",
            datatype={numpy.dtype(float): numpy.dtype("float32")},
        )
        g = cfdm.read(tmpfile)[0]
        self.assertEqual(
            g.data.dtype,
            numpy.dtype("float32"),
            "datatype read in is " + str(g.data.dtype),
        )

    def test_read_write_unlimited(self):
        """Test reading and writing with an unlimited dimension."""
        for fmt in self.netcdf_fmts:

            f = cfdm.read(self.filename)[0]
            domain_axes = f.domain_axes()

            domain_axes["domainaxis0"].nc_set_unlimited(True)
            cfdm.write(f, tmpfile, fmt=fmt)

            f = cfdm.read(tmpfile)[0]
            domain_axes = f.domain_axes()
            self.assertTrue(domain_axes["domainaxis0"].nc_is_unlimited())

        f = cfdm.read(self.filename)[0]

        domain_axes = f.domain_axes()

        domain_axes["domainaxis0"].nc_set_unlimited(True)
        domain_axes["domainaxis2"].nc_set_unlimited(True)
        cfdm.write(f, tmpfile, fmt="NETCDF4")

        f = cfdm.read(tmpfile)[0]
        domain_axes = f.domain_axes()
        self.assertTrue(domain_axes["domainaxis0"].nc_is_unlimited())
        self.assertTrue(domain_axes["domainaxis2"].nc_is_unlimited())

    def test_read_CDL(self):
        """Test the reading of files in CDL format."""
        subprocess.run(
            " ".join(["ncdump", self.filename, ">", tmpfile]),
            shell=True,
            check=True,
        )

        # For the cases of '-h' and '-c', i.e. only header info or coordinates,
        # notably no data, take two cases each: one where there is sufficient
        # info from the metadata to map to fields, and one where there isn't:
        #     1. Sufficient metadata, so should be read-in successfully
        subprocess.run(
            " ".join(["ncdump", "-h", self.filename, ">", tmpfileh]),
            shell=True,
            check=True,
        )
        subprocess.run(
            " ".join(["ncdump", "-c", self.filename, ">", tmpfilec]),
            shell=True,
            check=True,
        )

        #     2. Insufficient metadata, so should error with a message as such
        geometry_1_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "geometry_1.nc"
        )
        subprocess.run(
            " ".join(["ncdump", "-h", geometry_1_file, ">", tmpfileh2]),
            shell=True,
            check=True,
        )
        subprocess.run(
            " ".join(["ncdump", "-c", geometry_1_file, ">", tmpfilec2]),
            shell=True,
            check=True,
        )

        f0 = cfdm.read(self.filename)[0]

        # Case (1) as above, so read in and check the fields are as should be
        f = cfdm.read(tmpfile)[0]
        cfdm.read(tmpfileh)[0]
        c = cfdm.read(tmpfilec)[0]

        # Case (2) as above, so the right error should be raised on read
        with self.assertRaises(ValueError):
            cfdm.read(tmpfileh2)[0]

        with self.assertRaises(ValueError):
            cfdm.read(tmpfilec2)[0]

        self.assertTrue(f0.equals(f, verbose=3))

        self.assertTrue(
            f.construct("grid_latitude").equals(
                c.construct("grid_latitude"), verbose=3
            )
        )
        self.assertTrue(
            f0.construct("grid_latitude").equals(
                c.construct("grid_latitude"), verbose=3
            )
        )

        with self.assertRaises(OSError):
            cfdm.read("test_read_write.py")

        # TODO: make portable instead of skipping on Mac OS (see Issue #25):
        #       '-i' aspect solved, but the regex patterns need amending too.
        if platform.system() != "Darwin":  # False for Mac OS(X) only
            for regex in [
                r'"1 i\ \ "',
                r'"1 i\// comment"',
                r'"1 i\ // comment"',
                r'"1 i\ \t// comment"',
            ]:
                # Note that really we just want to do an in-place sed
                # ('sed -i') but because of subtle differences between the
                # GNU (Linux OS) and BSD (some Mac OS) command variants a
                # safe portable one-liner may not be possible. This will
                # do, overwriting the intermediate file. The '-E' to mark
                # as an extended regex is also for portability.
                subprocess.run(
                    " ".join(
                        [
                            "sed",
                            "-E",
                            "-e",
                            regex,
                            tmpfileh,
                            ">" + tmpfileh3,
                            "&&",
                            "mv",
                            tmpfileh3,
                            tmpfileh,
                        ]
                    ),
                    shell=True,
                    check=True,
                )

                cfdm.read(tmpfileh)[0]

        # Finally test an invalid CDL input
        with open(tmpfilec3, "w") as file:
            file.write("netcdf test_file {\n  add badness\n}")
        # TODO: work out (if it is even possible in a farily simple way) how
        # to suppress the expected error in stderr of the ncdump command
        # called by cfdm.read under the hood. Note that it can be easily
        # suppressed at subprocess call-time (but we don't want to do that in
        # case of genuine errors) and the following doesn't work as it doesn't
        # influence the subprocess: with contextlib.redirect_stdout(os.devnull)
        with self.assertRaises(ValueError):
            cfdm.read(tmpfilec3)

    def test_read_write_string(self):
        """Test the `string` keyword argument to `read` and `write`."""
        f = cfdm.read(self.string_filename)

        n = int(len(f) / 2)

        for i in range(0, n):
            j = i + n
            self.assertTrue(
                f[i].data.equals(f[j].data, verbose=3),
                f"{f[i]!r} {f[j]!r}",
            )
            self.assertTrue(
                f[j].data.equals(f[i].data, verbose=3),
                f"{f[j]!r} {f[i]!r}",
            )

        # Note: Don't loop round all netCDF formats for better
        #       performance. Just one netCDF3 and one netCDF4 format
        #       is sufficient to test the functionality

        f0 = cfdm.read(self.string_filename)
        for string0 in (True, False):
            for fmt0 in ("NETCDF4", "NETCDF3_CLASSIC"):
                cfdm.write(f0, tmpfile0, fmt=fmt0, string=string0)

                for string1 in (True, False):
                    for fmt1 in ("NETCDF4", "NETCDF3_CLASSIC"):
                        cfdm.write(f0, tmpfile1, fmt=fmt1, string=string1)

                        for i, j in zip(
                            cfdm.read(tmpfile1), cfdm.read(tmpfile0)
                        ):
                            self.assertTrue(i.equals(j, verbose=3))

    def test_read_write_Conventions(self):
        """Test the `Conventions` keyword argument to `write`."""
        f = cfdm.read(self.filename)[0]

        version = "CF-" + cfdm.CF()
        other = "ACDD-1.3"

        for Conventions in (other,):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertEqual(
                g.get_property("Conventions"),
                " ".join([version, other]),
                f"{g.get_property('Conventions')!r}, {Conventions!r}",
            )

        for Conventions in (
            version,
            "",
            " ",
            ",",
            ", ",
        ):
            Conventions = version
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertEqual(
                g.get_property("Conventions"),
                version,
                f"{g.get_property('Conventions')!r}, {Conventions!r}",
            )

        for Conventions in (
            [version],
            [version, other],
        ):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertEqual(
                g.get_property("Conventions"),
                " ".join(Conventions),
                f"{g.get_property('Conventions')!r}, {Conventions!r}",
            )

        for Conventions in ([other, version],):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertEqual(
                g.get_property("Conventions"),
                " ".join([version, other]),
                f"{g.get_property('Conventions')!r}, {Conventions!r}",
            )

    def test_read_write_multiple_geometries(self):
        """Test reading and writing with a mixture of geometry cells."""
        a = []
        for filename in (
            "geometry_1.nc",
            "geometry_2.nc",
            "geometry_3.nc",
            "geometry_4.nc",
            "geometry_interior_ring_2.nc",
            "geometry_interior_ring.nc",
        ):
            a.extend(cfdm.read(filename))

        for n, f in enumerate(a):
            f.set_property("test_id", str(n))

        cfdm.write(a, tmpfile, verbose=1)

        f = cfdm.read(tmpfile, verbose=1)

        self.assertEqual(len(a), len(f))

        for x in a:
            for n, y in enumerate(f[:]):
                if x.equals(y):
                    f.pop(n)
                    break

        self.assertFalse(f)

    def test_read_write_domain(self):
        """TODO DOCS."""
        f = cfdm.example_field(1)
        d = f.domain.copy()

        # 1 domain
        cfdm.write(d, tmpfile)
        e = cfdm.read(tmpfile)
        self.assertTrue(len(e), 10)

        e = cfdm.read(tmpfile, domain=True, verbose=1)
        self.assertEqual(len(e), 1)
        e = e[0]
        self.assertIsInstance(e, cfdm.Domain)
        self.assertTrue(e.equals(e.copy(), verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

        # 1 field and 1 domain
        cfdm.write([f, d], tmpfile)
        g = cfdm.read(tmpfile)
        self.assertTrue(len(g), 1)
        g = g[0]
        self.assertIsInstance(g, cfdm.Field)
        self.assertTrue(g.equals(f, verbose=3))

        e = cfdm.read(tmpfile, domain=True, verbose=1)
        self.assertEqual(len(e), 1)
        e = e[0]
        self.assertIsInstance(e, cfdm.Domain)

        # 1 field and 2 domains
        cfdm.write([f, d, d], tmpfile)
        g = cfdm.read(tmpfile)
        self.assertTrue(len(g), 1)
        g = g[0]
        self.assertIsInstance(g, cfdm.Field)
        self.assertTrue(g.equals(f, verbose=3))

        e = cfdm.read(tmpfile, domain=True, verbose=1)
        self.assertEqual(len(e), 2)
        self.assertIsInstance(e[0], cfdm.Domain)
        self.assertIsInstance(e[1], cfdm.Domain)
        self.assertTrue(e[0].equals(e[1]))

    def test_write_coordinates(self):
        """Test the `coordinates` keyword argument of `write`."""
        f = cfdm.example_field(0)

        cfdm.write(f, tmpfile, coordinates=True)
        g = cfdm.read(tmpfile)

        self.assertEqual(len(g), 1)
        self.assertTrue(g[0].equals(f, verbose=3))

    def test_write_scalar_domain_ancillary(self):
        """Test the writing of a file with a scalar domain ancillary."""
        f = cfdm.example_field(1)

        # Create scalar domain ancillary
        d = f.construct("ncvar%a")
        d.del_data()
        d.set_data(10)
        d.del_bounds()

        key = f.construct_key("ncvar%a")
        f.set_data_axes((), key=key)

        cfdm.write(f, tmpfile)

    def test_write_filename_expansion(self):
        """Test the writing to a file name that requires expansions."""
        f = cfdm.example_field(0)
        filename = os.path.join("$PWD", os.path.basename(tmpfile))
        cfdm.write(f, filename)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
