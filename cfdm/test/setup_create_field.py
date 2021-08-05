import datetime
import faulthandler
import os
import unittest

import numpy

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

verbose = False
warnings = False


class create_fieldTest(unittest.TestCase):
    """Test ab initio creation of field constructs in memory."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )

        try:
            os.remove(self.filename)
        except Exception:
            pass

    def test_create_field(self):
        """Test ab initio creation of a first variation of field."""
        # Dimension coordinates
        dim1 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(10.0)))
        dim1.set_property("standard_name", "grid_latitude")
        dim1.set_property("units", "degrees")

        data = numpy.arange(9.0) + 20
        data[-1] = 34
        dim0 = cfdm.DimensionCoordinate(data=cfdm.Data(data))
        dim0.set_property("standard_name", "grid_longitude")
        dim0.set_property("units", "degrees")
        dim0.nc_set_variable("x")

        array = dim0.data.array

        array = numpy.array([array - 0.5, array + 0.5]).transpose((1, 0))
        array[-2, 1] = 30
        array[-1, :] = [30, 36]
        dim0.set_bounds(cfdm.Bounds(data=cfdm.Data(array)))

        dim2 = cfdm.DimensionCoordinate(
            data=cfdm.Data([1.5]),
            bounds=cfdm.Bounds(data=cfdm.Data([[1, 2.0]])),
        )
        dim2.set_property(
            "standard_name", "atmosphere_hybrid_height_coordinate"
        )
        dim2.set_property("computed_standard_name", "altitude")

        # Auxiliary coordinates
        ak = cfdm.DomainAncillary(data=cfdm.Data([10.0]))
        ak.set_property("units", "m")
        ak.id = "atmosphere_hybrid_height_coordinate_ak"
        ak.set_bounds(cfdm.Bounds(data=cfdm.Data([[5, 15.0]])))

        bk = cfdm.DomainAncillary(data=cfdm.Data([20.0]))
        bk.id = "atmosphere_hybrid_height_coordinate_bk"
        bk.set_bounds(cfdm.Bounds(data=cfdm.Data([[14, 26.0]])))

        aux2 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(-45, 45, dtype="int32").reshape(10, 9))
        )
        aux2.set_property("units", "degree_N")
        aux2.set_property("standard_name", "latitude")

        aux3 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(60, 150, dtype="int32").reshape(9, 10))
        )
        aux3.set_property("standard_name", "longitude")
        aux3.set_property("units", "degreeE")

        array = numpy.ma.array(
            [
                "alpha",
                "beta",
                "gamma",
                "delta",
                "epsilon",
                "zeta",
                "eta",
                "theta",
                "iota",
                "kappa",
            ],
            dtype="S",
        )
        array[0] = numpy.ma.masked
        aux4 = cfdm.AuxiliaryCoordinate(data=cfdm.Data(array))
        aux4.set_property("long_name", "greek_letters")

        # Cell measures
        msr0 = cfdm.CellMeasure(
            data=cfdm.Data(1 + numpy.arange(90.0).reshape(9, 10) * 1234)
        )
        msr0.set_measure("area")
        msr0.set_property("units", "km2")
        msr0.nc_set_variable("areacella")

        # Data
        data = cfdm.Data(numpy.arange(90.0).reshape(10, 9))

        properties = {"units": "m s-1"}

        f = cfdm.Field(properties=properties)
        f.set_property("standard_name", "eastward_wind")

        da = cfdm.DomainAxis(9)
        da.nc_set_dimension("grid_longitude")
        axisX = f.set_construct(da)
        axisY = f.set_construct(cfdm.DomainAxis(10))
        axisZ = f.set_construct(cfdm.DomainAxis(1))

        f.set_data(data, axes=[axisY, axisX])

        x = f.set_construct(dim0, axes=axisX)
        y = f.set_construct(dim1, axes=axisY)
        z = f.set_construct(dim2, axes=[axisZ])

        lat = f.set_construct(aux2, axes=[axisY, axisX])
        lon = f.set_construct(aux3, axes=[axisX, axisY])
        f.set_construct(aux4, axes=[axisY])

        ak = f.set_construct(ak, axes=axisZ)
        bk = f.set_construct(bk, axes=[axisZ])

        # Coordinate references
        coordinate_conversion = cfdm.CoordinateConversion(
            parameters={
                "grid_mapping_name": "rotated_latitude_longitude",
                "grid_north_pole_latitude": 38.0,
                "grid_north_pole_longitude": 190.0,
            }
        )

        datum = cfdm.Datum(parameters={"earth_radius": 6371007})

        ref0 = cfdm.CoordinateReference(
            coordinate_conversion=coordinate_conversion,
            datum=datum,
            coordinates=[x, y, lat, lon],
        )

        f.set_construct(msr0, axes=[axisX, axisY])

        f.set_construct(ref0)

        orog = cfdm.DomainAncillary(data=f.get_data())
        orog.set_property("standard_name", "surface_altitude")
        orog.set_property("units", "m")
        orog = f.set_construct(orog, axes=[axisY, axisX])

        coordinate_conversion = cfdm.CoordinateConversion(
            parameters={
                "standard_name": "atmosphere_hybrid_height_coordinate",
                "computed_standard_name": "altitude",
            },
            domain_ancillaries={"orog": orog, "a": ak, "b": bk},
        )

        ref1 = cfdm.CoordinateReference(
            coordinates=[z],
            datum=datum,
            coordinate_conversion=coordinate_conversion,
        )

        ref1 = f.set_construct(ref1)

        # Field ancillary variables
        g = f.copy()
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.set_property("standard_name", "ancillaryA")
        f.set_construct(anc, axes=[axisY, axisX])

        g = f[0]
        g = g.squeeze()
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.set_property("long_name", "ancillaryB")
        f.set_construct(anc, axes=axisX)

        g = f[..., 0]
        g = g.squeeze()
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.set_property("foo", "bar")
        f.set_construct(anc, axes=[axisY])

        f.set_property("flag_values", numpy.array([1, 2, 4], "int32"))
        f.set_property("flag_meanings", "a bb ccc")
        f.set_property("flag_masks", [2, 1, 0])

        cm0 = cfdm.CellMethod(
            axes=axisX,
            method="mean",
            qualifiers={"interval": [cfdm.Data(1, "day")], "comment": "ok"},
        )

        cm1 = cfdm.CellMethod(
            axes=[axisY], method="maximum", qualifiers={"where": "sea"}
        )

        f.set_construct(cm0)
        f.set_construct(cm1)

        self.assertTrue(
            f.equals(f, verbose=verbose), "Field f not equal to itself"
        )

        self.assertTrue(
            f.equals(f.copy(), verbose=verbose),
            "Field f not equal to a copy of itself",
        )

        cfdm.write(f, self.filename, fmt="NETCDF3_CLASSIC", verbose=verbose)

        g = cfdm.read(self.filename, verbose=1)

        array = (
            g[0]
            .constructs.filter_by_identity("long_name=greek_letters")
            .value()
            .data.array
        )
        self.assertEqual(array[1], b"beta")

        self.assertEqual(len(g), 1)

        g = g[0].squeeze()

        self.assertEqual(
            sorted(f.constructs),
            sorted(g.constructs),
            f"\n\nf (created in memory)"
            f"\n{f.constructs}"
            f"\n\n{f.constructs.items()}"
            f"\n\ng (read from disk)"
            f"\n{g.constructs}"
            f"\n\n{g.constructs.items()}",
        )

        self.assertTrue(
            f.equals(f, verbose=verbose),
            "Field f not equal to itself after having been written to disk",
        )

        self.assertTrue(
            f.equals(f.copy(), verbose=verbose),
            "Field f not equal to a copy of itself after having been "
            "written to disk",
        )

        self.assertTrue(
            g.equals(g.copy(), verbose=verbose),
            "Field g not equal to a copy of itself",
        )

        self.assertTrue(
            g.equals(f, verbose=verbose),
            "Field (f) not equal to itself read back in (g)",
        )

        x = g.dump(display=False)
        x = f.dump(display=False)

        g = cfdm.read(
            self.filename,
            verbose=verbose,
            extra="domain_ancillary",
            warnings=warnings,
        )


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
