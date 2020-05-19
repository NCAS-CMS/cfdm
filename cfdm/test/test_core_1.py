from __future__ import print_function
import datetime
import os
import sys
import unittest

import numpy

import cfdm

verbose = False


class create_fieldTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or calls (those
        # without a 'verbose' option to do the same) e.g. to debug them, wrap
        # them (for methods, start-to-end internally) as follows:
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

    def test_core_create_field(self):
        # Dimension coordinates
        dim1 = cfdm.core.DimensionCoordinate(data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.arange(10.))))
        dim1.set_property('standard_name', 'grid_latitude')
        dim1.set_property('units', 'degrees')

        data = numpy.arange(9.) + 20
        data[-1] = 34
        dim0 = cfdm.core.DimensionCoordinate(data=cfdm.core.Data(cfdm.core.NumpyArray(data)))
        dim0.set_property('standard_name', 'grid_longitude')
        dim0.set_property('units', 'degrees')

        array = dim0.data.array

        array = numpy.array([array-0.5, array+0.5]).transpose((1,0))
        array[-2, 1] = 30
        array[-1, :] = [30, 36]
        dim0.set_bounds(cfdm.core.Bounds(data=cfdm.core.Data(cfdm.core.NumpyArray(array))))

        dim2 = cfdm.core.DimensionCoordinate(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([1.5]))),
            bounds=cfdm.core.Bounds(data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([[1, 2.]])))))
        dim2.set_property('standard_name'         , 'atmosphere_hybrid_height_coordinate')
        dim2.set_property('computed_standard_name', 'altitude')

        # Auxiliary coordinates
        ak = cfdm.core.DomainAncillary(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([10.]))))
        ak.set_property('units', 'm')
        ak.set_bounds(cfdm.core.Bounds(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([[5, 15.]])))))

        bk = cfdm.core.DomainAncillary(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([20.]))))
        bk.set_bounds(cfdm.core.Bounds(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([[14, 26.]])))))

        aux2 = cfdm.core.AuxiliaryCoordinate(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.arange(-45, 45, dtype='int32').reshape(10, 9))))
        aux2.set_property('units', 'degree_N')
        aux2.set_property('standard_name', 'latitude')

        aux3 = cfdm.core.AuxiliaryCoordinate(
            data=cfdm.core.Data(cfdm.core.NumpyArray(numpy.arange(60, 150, dtype='int32').reshape(9, 10))))
        aux3.set_property('standard_name', 'longitude')
        aux3.set_property('units', 'degreeE')

        array = numpy.ma.array(['alpha','beta','gamma','delta','epsilon',
                                'zeta','eta','theta','iota','kappa'], dtype='S')
        array[0] = numpy.ma.masked
        aux4 = cfdm.core.AuxiliaryCoordinate(data=cfdm.core.Data(cfdm.core.NumpyArray(array)))
        aux4.set_property('long_name', 'greek_letters')

        # Cell measures
        msr0 = cfdm.core.CellMeasure(
            data=cfdm.core.Data(cfdm.core.NumpyArray(1+numpy.arange(90.).reshape(9, 10)*1234)))
        msr0.set_measure('area')
        msr0.set_property('units', 'km2')

        # Data
        data = cfdm.core.Data(cfdm.core.NumpyArray(numpy.arange(90.).reshape(10, 9)))

        properties = {'units': 'm s-1'}

        f = cfdm.core.Field(properties=properties)
        f.set_property('standard_name', 'eastward_wind')

        axisX = f.set_construct(cfdm.core.DomainAxis(9))
        axisY = f.set_construct(cfdm.core.DomainAxis(10))
        axisZ = f.set_construct(cfdm.core.DomainAxis(1))

        f.set_data(data, axes=[axisY, axisX])

        x = f.set_construct(dim0, axes=[axisX])
        y = f.set_construct(dim1, axes=[axisY])
        z = f.set_construct(dim2, axes=[axisZ])

        lat   = f.set_construct(aux2, axes=[axisY, axisX])
        lon   = f.set_construct(aux3, axes=[axisX, axisY])
        greek = f.set_construct(aux4, axes=[axisY])

        ak = f.set_construct(ak, axes=[axisZ])
        bk = f.set_construct(bk, axes=[axisZ])

        # Coordinate references
        coordinate_conversion = cfdm.core.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'grid_north_pole_latitude': 38.0,
                        'grid_north_pole_longitude': 190.0})

        datum = cfdm.core.Datum(parameters={'earth_radius': 6371007})

        ref0 = cfdm.core.CoordinateReference(
            coordinate_conversion=coordinate_conversion,
            datum=datum,
            coordinates=[x, y, lat, lon]
        )

        f.set_construct(msr0, axes=[axisX, axisY])

        f.set_construct(ref0)

        orog = cfdm.core.DomainAncillary(data=f.get_data())
        orog.set_property('standard_name', 'surface_altitude')
        orog.set_property('units', 'm')
        orog = f.set_construct(orog, axes=[axisY, axisX])

        coordinate_conversion = cfdm.core.CoordinateConversion(
            parameters={'standard_name': 'atmosphere_hybrid_height_coordinate',
                        'computed_standard_name': 'altitude'},
            domain_ancillaries={'orog': orog,
                                'a'   : ak,
                                'b'   : bk})

        ref1 = cfdm.core.CoordinateReference(
            coordinates=[z],
            datum=datum,
            coordinate_conversion=coordinate_conversion
        )

        ref1 = f.set_construct(ref1)

        f_data = f.data

        # Field ancillary variables
        data = f_data
        anc = cfdm.core.FieldAncillary(data=data)
        f.set_construct(anc, axes=[axisY, axisX])

        data = f_data.array[0]
        anc = cfdm.core.FieldAncillary(data=cfdm.core.Data(cfdm.core.NumpyArray(data)))
        f.set_construct(anc, axes=[axisX])

        data = f_data.array[..., 0]
        anc = cfdm.core.FieldAncillary(data=cfdm.core.Data(cfdm.core.NumpyArray(data)))
        f.set_construct(anc, axes=[axisY])

        f.set_property('flag_values', numpy.array([1, 2, 4], 'int32'))
        f.set_property('flag_meanings', 'a bb ccc')
        f.set_property('flag_masks', [2, 1, 0])

        cm0 = cfdm.core.CellMethod(
            axes=[axisX],
            method='mean',
            qualifiers={
                'interval': [cfdm.core.Data(cfdm.core.NumpyArray(numpy.array(1)), 'day')],
                'comment' : 'ok'})

        cm1 = cfdm.core.CellMethod(
            axes=[axisY],
            method='maximum',
            qualifiers={'where' : 'sea'})

        f.set_construct(cm0)
        f.set_construct(cm1)


    def test_core_FUNCTIONS(self):
        self.assertTrue(cfdm.core.CF() == cfdm.core.__cf_version__)
        _ = cfdm.core.environment(display=False)


#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
