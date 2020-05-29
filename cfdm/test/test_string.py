from __future__ import print_function
import datetime
import inspect
import os
import tempfile
import unittest

import numpy

import cfdm


class StringTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.LOG_LEVEL('DISABLE')

        self.test_only = []

        (fd, self.tempfilename) = tempfile.mkstemp(
            suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)


    def tearDown(self):
        os.remove(self.tempfilename)


    def test_STRING(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for array in (numpy.ma.array(list('abcdefghij'), dtype='S'),
                      numpy.ma.array(['a', 'b1', 'c12', 'd123', 'e1234',
                                      'f', 'g', 'h', 'i', 'j'], dtype='S')):

            # Initialize the field
            tas = cfdm.Field(
                properties={'project': 'research',
                            'standard_name': 'air_temperature',
                            'units': 'K'})

            # Create and set domain axes
            axis_T = tas.set_construct(cfdm.DomainAxis(1))
            axis_Z = tas.set_construct(cfdm.DomainAxis(1))
            axis_Y = tas.set_construct(cfdm.DomainAxis(10))
            axis_X = tas.set_construct(cfdm.DomainAxis(9))

            # Set the field data
            tas.set_data(cfdm.Data(numpy.arange(90.).reshape(10, 9)),
                         axes=[axis_Y, axis_X])

            # Create and set the dimension coordinates
            dimension_coordinate_Y = cfdm.DimensionCoordinate(
                properties={'standard_name': 'grid_latitude',
                            'units': 'degrees'},
                data=cfdm.Data(numpy.arange(10.)),
                bounds=cfdm.Bounds(
                    data=cfdm.Data(numpy.arange(20).reshape(10, 2))))

            dimension_coordinate_X = cfdm.DimensionCoordinate(
                properties={'standard_name': 'grid_longitude',
                        'units': 'degrees'},
                data=cfdm.Data(numpy.arange(9.)),
                bounds=cfdm.Bounds(
                    data=cfdm.Data(numpy.arange(18).reshape(9, 2))))

            dim_Y = tas.set_construct(dimension_coordinate_Y, axes=[axis_Y])
            dim_X = tas.set_construct(dimension_coordinate_X, axes=[axis_X])

            # Create and set the auxiliary coordinates
            array[0] = numpy.ma.masked
            aux0 = cfdm.AuxiliaryCoordinate(
                properties={'long_name': 'Grid latitude name'},
                data=cfdm.Data(array))

            tas.set_construct(aux0, axes=[axis_Y])

            cfdm.write(tas, self.tempfilename)

            tas1 = cfdm.read(self.tempfilename)[0]

            aux1 = tas1.constructs.filter_by_identity(
                'long_name=Grid latitude name').value()
            self.assertEqual(aux0.data.shape, array.shape, aux0.data.shape)
            self.assertEqual(aux1.data.shape, array.shape, aux1.data.shape)
        #--- End: for


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
