import datetime
import os
import time
import unittest

import numpy

import cfdm

class AuxiliaryCoordinateTest(unittest.TestCase):
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
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')
        aux1 = cfdm.AuxiliaryCoordinate()
        aux1.standard_name = 'latitude'
        a = numpy.array([-30, -23.5, -17.8123, -11.3345, -0.7, -0.2, 0, 0.2, 0.7, 11.30003, 17.8678678, 23.5, 30])
        aux1.set_data(cfdm.Data(a, 'degrees_north'))
        bounds = cfdm.Bounds()
        b = numpy.empty(a.shape + (2,))
        b[:, 0] = a - 0.1
        b[:, 1] = a + 0.1
        bounds.set_data(cfdm.Data(b))
        aux1.set_bounds(bounds)
        self.aux1 = aux1


    def test_AuxiliaryCoordinate__repr__str__dump(self):
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates('latitude').value()

        _ = repr(x)
        _ = str(x)
        _ = x.dump(display=False)


    def test_AuxiliaryCoordinate_bounds(self):
        f = cfdm.read(self.filename)[0]

        d = f.dimension_coordinates('grid_longitude').value()
        x = cfdm.AuxiliaryCoordinate(source=d)


    def test_AuxiliaryCoordinate_properties(self):
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates('latitude').value()

        x.positive = 'up'
        self.assertTrue(x.positive == 'up')
        del x.positive
        self.assertIsNone(getattr(x, 'positive', None))

        x.axis = 'Z'
        self.assertTrue(x.axis == 'Z')
        del x.axis
        self.assertIsNone(getattr(x, 'axis', None))

        d = f.dimension_coordinates('grid_longitude').value()
        x = cfdm.AuxiliaryCoordinate(source=d)

    def test_AuxiliaryCoordinate_insert_dimension(self):
        f = cfdm.read(self.filename)[0]
        d = f.dimension_coordinates('grid_longitude').value()
        x = cfdm.AuxiliaryCoordinate(source=d)

        self.assertTrue(x.shape == (9,))
        self.assertTrue(x.bounds.shape == (9, 2))

        y = x.insert_dimension(0)
        self.assertTrue(y.shape == (1, 9))
        self.assertTrue(y.bounds.shape == (1, 9, 2), y.bounds.shape)

        x.insert_dimension(-1, inplace=True)
        self.assertTrue(x.shape == (9, 1))
        self.assertTrue(x.bounds.shape == (9, 1, 2), x.bounds.shape)


    def test_AuxiliaryCoordinate_transpose(self):
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates('longitude').value()

        bounds = cfdm.Bounds(data=cfdm.Data(numpy.arange(9*10*4).reshape(9, 10, 4)))
        x.set_bounds(bounds)

        self.assertTrue(x.shape == (9, 10))
        self.assertTrue(x.bounds.shape == (9, 10, 4))

        y = x.transpose()
        self.assertTrue(y.shape == (10, 9))
        self.assertTrue(y.bounds.shape == (10, 9, 4), y.bounds.shape)

        x.transpose([1, 0], inplace=True)
        self.assertTrue(x.shape == (10, 9))
        self.assertTrue(x.bounds.shape == (10, 9, 4), x.bounds.shape)


    def test_AuxiliaryCoordinate_squeeze(self):
        f = cfdm.read(self.filename)[0]
        x = f.auxiliary_coordinates('longitude').value()

        bounds = cfdm.Bounds(data=cfdm.Data(numpy.arange(9*10*4).reshape(9, 10, 4)))
        x.set_bounds(bounds)
        x.insert_dimension(1, inplace=True)
        x.insert_dimension(0, inplace=True)

        self.assertTrue(x.shape == (1, 9, 1, 10))
        self.assertTrue(x.bounds.shape == (1, 9, 1, 10, 4))

        y = x.squeeze()
        self.assertTrue(y.shape == (9, 10))
        self.assertTrue(y.bounds.shape == (9, 10, 4), y.bounds.shape)

        x.squeeze(2, inplace=True)
        self.assertTrue(x.shape == (1, 9, 10))
        self.assertTrue(x.bounds.shape == (1, 9, 10, 4), x.bounds.shape)


#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
