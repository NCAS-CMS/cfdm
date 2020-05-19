from __future__ import print_function
import datetime
import os
import sys
import unittest

import numpy

import cfdm

verbose  = False
warnings = False


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

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file_c.nc')

    def test_create_field_3(self):

        # Dimension coordinates
        data = numpy.arange(9.) + 20
        data[-1] = 34
        dim0 = cfdm.DimensionCoordinate(data=cfdm.Data(data))
        dim0.set_property('standard_name', 'grid_longitude')
        dim0.set_property('units', 'degrees')

        array = dim0.data.array

        array = numpy.array([array-0.5, array+0.5]).transpose((1,0))
        array[-2, 1] = 30
        array[-1, :] = [30, 36]
        dim0.set_bounds(cfdm.Bounds(data=cfdm.Data(array)))

        dim1 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(10.)))
        dim1.set_property('standard_name', 'grid_latitude')
        dim1.set_property('units', 'degrees')

        dim2 = cfdm.DimensionCoordinate(data=cfdm.Data([1.5]),
                                        bounds=cfdm.Bounds(data=cfdm.Data([[1, 2.]])))
        dim2.set_property('standard_name'         , 'atmosphere_hybrid_height_coordinate')
        dim2.set_property('computed_standard_name', 'altitude')

        dim3 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.array([15.0])))
        dim3.set_property('standard_name', 'time')
        dim3.set_property('units', 'days since 2004-06-01')

        dim3.set_bounds(cfdm.Bounds(data=cfdm.Data([[0, 30.]])))

#        dim3.set_geometry('climatology')

        # Auxiliary coordinates
        ak = cfdm.DomainAncillary(data=cfdm.Data([10.]))
        ak.set_property('units', 'm')
        ak.set_bounds(cfdm.Bounds(data=cfdm.Data([[5, 15.]])))

        bk = cfdm.DomainAncillary(data=cfdm.Data([20.]))
        bk.set_bounds(cfdm.Bounds(data=cfdm.Data([[14, 26.]])))

        aux2 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(-45, 45, dtype='int32').reshape(10, 9)))
        aux2.set_property('units', 'degree_N')
        aux2.set_property('standard_name', 'latitude')

        aux3 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(60, 150, dtype='int32').reshape(9, 10)))
        aux3.set_property('standard_name', 'longitude')
        aux3.set_property('units', 'degreeE')

        array = numpy.ma.array(['alpha','beta','gamma','delta','epsilon',
                                'zeta','eta','theta','iota','kappa'], dtype='S')
        array[0] = numpy.ma.masked
        aux4 = cfdm.AuxiliaryCoordinate(data=cfdm.Data(array))
        aux4.set_property('standard_name', 'greek_letters')

        # Cell measures
        msr0 = cfdm.CellMeasure(
            data=cfdm.Data(1+numpy.arange(90.).reshape(9, 10)*1234))
        msr0.set_measure('area')
        msr0.set_property('units', 'km2')

        # Data
        data = cfdm.Data(numpy.arange(90.).reshape(10, 9))

        properties = {'units': 'm s-1'}

        f = cfdm.Field(properties=properties)
        f.set_property('standard_name', 'eastward_wind')

        axisX = f.set_construct(cfdm.DomainAxis(9))
        axisY = f.set_construct(cfdm.DomainAxis(10))
        axisZ = f.set_construct(cfdm.DomainAxis(1))
        axisT = f.set_construct(cfdm.DomainAxis(1))

        f.set_data(data, axes=[axisY, axisX])

        x = f.set_construct(dim0, axes=[axisX])
        y = f.set_construct(dim1, axes=[axisY])
        z = f.set_construct(dim2, axes=[axisZ])
        t = f.set_construct(dim3, axes=[axisT])

        lat   = f.set_construct(aux2, axes=[axisY, axisX])
        lon   = f.set_construct(aux3, axes=[axisX, axisY])
        greek = f.set_construct(aux4, axes=[axisY])

        ak = f.set_construct(ak, axes=[axisZ])
        bk = f.set_construct(bk, axes=[axisZ])

       # Coordinate references
#       ref0 = cfdm.CoordinateReference(
#           parameters={'grid_mapping_name': 'rotated_latitude_longitude',
#                       'grid_north_pole_latitude': 38.0,
#                       'grid_north_pole_longitude': 190.0,
#                       'earth_radius': 6371007,},
#           coordinates=[x, y, lat, lon]
#       )

        coordinate_conversion = cfdm.CoordinateConversion(
            parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                        'grid_north_pole_latitude': 38.0,
                        'grid_north_pole_longitude': 190.0})

        datum = cfdm.Datum(parameters={'earth_radius': 6371007})

        ref0 = cfdm.CoordinateReference(
            coordinate_conversion=coordinate_conversion,
            datum=datum,
            coordinates=[x, y, lat, lon]
            )

        f.set_construct(msr0, axes=[axisX, axisY])

        f.set_construct(ref0)

        orog = cfdm.DomainAncillary(data=f.get_data())
        orog.set_property('standard_name', 'surface_altitude')
        orog.set_property('units', 'm')
        orog = f.set_construct(orog, axes=[axisY, axisX])

        datum1 = cfdm.Datum({'earth_radius' : 6371007})

        coordinate_conversion1 = cfdm.CoordinateConversion(
            parameters={'standard_name': 'atmosphere_hybrid_height_coordinate',
                        'computed_standard_name': 'altitude'},
            domain_ancillaries={'orog': orog,
                                'a'   : ak,
                                'b'   : bk})

        ref1 = cfdm.CoordinateReference(
            datum=datum1,
            coordinate_conversion=coordinate_conversion1,
            coordinates=[z]
        )

        ref1 = f.set_construct(ref1)

        # Field ancillary variables
#        g = f.transpose([1, 0])
        g = f.copy()
#        g.standard_name = 'ancillary0'
#        g *= 0.01
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.standard_name = 'ancillaryA'
        f.set_construct(anc, axes=[axisY, axisX])

        g = f[0]
        g = g.squeeze()
#        g.standard_name = 'ancillary2'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.standard_name = 'ancillaryB'
        f.set_construct(anc, axes=[axisX])

        g = f[..., 0]
        g = g.squeeze()
#        g.standard_name = 'ancillary3'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.get_data())
        anc.standard_name = 'ancillaryC'
        f.set_construct(anc, axes=[axisY])


        f.set_property('flag_values', numpy.array([1, 2, 4], 'int32'))
        f.set_property('flag_meanings', 'a bb ccc')
        f.set_property('flag_masks', [2, 1, 0])

        cm0 =  cfdm.CellMethod(axes=[axisX],
                               method='mean',
                               qualifiers={'interval': [cfdm.Data(1, 'day')],
                                           'comment' : 'ok'})

        cm1 =  cfdm.CellMethod(axes=[axisY],
                               method='maximum',
                               qualifiers={'where' : 'sea'})

        cm2 =  cfdm.CellMethod(axes=[axisT],
                               method='maximum',
                               qualifiers={'within' : 'years'})

        cm3 =  cfdm.CellMethod(axes=[axisT],
                               method='minimum',
                               qualifiers={'over' : 'years'})

        f.set_construct(cm0)
        f.set_construct(cm1)
        f.set_construct(cm2)
        f.set_construct(cm3)

        if verbose:
            print(repr(f))
            print(f)
            print(f.constructs)
            print(f.construct_data_axes())

            f.dump()

#        sys.exit(0)

        cfdm.write(f, self.filename, fmt='NETCDF3_CLASSIC', verbose=verbose)

        g = cfdm.read(self.filename, verbose=verbose) #, squeeze=True)

        if verbose:
#           g[0].dump()
#           sys.exit(0)
            for x in g:
                x.print_read_report()

        self.assertTrue(len(g) == 1, 'Read produced too many fields: {} != 1'.format(len(g)))

        g = g[0].squeeze()


#        print g
        self.assertTrue(sorted(f.constructs) == sorted(g.constructs),
                        '\n\nf (created in memory)\n{}\n\n{}\n\ng (read from disk)\n{}\n\n{}'.format(
                            sorted(f.constructs),
                            sorted(f.constructs.items()),
                            sorted(g.constructs),
                            sorted(g.constructs.items())))

        self.assertTrue(f.equals(f.copy(), verbose=verbose),
                        "Field f not equal to a copy of itself")

        self.assertTrue(g.equals(g.copy(), verbose=verbose),
                        "Field g not equal to a copy of itself")
#        print f.dump()

#        print'f'
#        print f
#        print 'g'
#        print g
#        f.dump()
#        g.dump()

        if verbose:
            f.dump()
            g.dump()
#        sys.exit(0)

        self.assertTrue(g.equals(f, verbose=verbose),
                        "Field not equal to itself read back in")

#        sys.exit(0)

        x = g.dump(display=False)
        x = f.dump(display=False)

        g = cfdm.read(self.filename, verbose=verbose,
                      extra=['domain_ancillary'], warnings=warnings)

        if verbose:
            for x in g:
                x.print_read_report()

            print(g)
            g[0].dump()
#        for x in g:
#            x.dump()
#        h = g.field('domainancillary2')
#        h.dump()
#        print h
#
#
#        h = g.field('domainancillary1')
#        print h
#
#        h = g.field('domainancillary0')
#        print h
#
#        h = g.field('cellmeasure0')
#        print h


#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
