import atexit
import datetime
import inspect
import os
import tempfile
import unittest

import numpy

import cfdm


n_tmpfiles = 1
tmpfiles = [tempfile.mkstemp('_test_string.nc', dir=os.getcwd())[1]
            for i in range(n_tmpfiles)]
(
    tempfile,
) = tmpfiles


def _remove_tmpfiles():
    '''Remove temporary files created during tests.

    '''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class StringTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.log_level('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.test_only = []

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

            cfdm.write(tas, tempfile)

            tas1 = cfdm.read(tempfile)[0]

            aux1 = tas1.constructs.filter_by_identity(
                'long_name=Grid latitude name').value()
            self.assertEqual(aux0.data.shape, array.shape, aux0.data.shape)
            self.assertEqual(aux1.data.shape, array.shape, aux1.data.shape)

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
