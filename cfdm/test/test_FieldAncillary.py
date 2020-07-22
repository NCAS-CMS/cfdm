import datetime
import os
import time
import unittest

import numpy

import cfdm


class FieldAncillaryTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.log_level('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_file.nc')

    def test_FieldAncillary__repr__str__dump(self):
        f = cfdm.read(self.filename)[0]
        x = f.field_ancillaries('ancillaryA').value()

        _ = repr(x)
        _ = str(x)
        self.assertIsInstance(x.dump(display=False), str)

    def test_FieldAncillary_source(self):
        f = cfdm.read(self.filename)[0]

        a = f.auxiliary_coordinates('latitude').value()
        x = cfdm.FieldAncillary(source=a)

    def test_FieldAncillary_properties(self):
        f = cfdm.read(self.filename)[0]
        x = f.domain_ancillaries('ncvar%a').value()

        x.set_property('long_name', 'qwerty')

        self.assertEqual(x.get_property('long_name'), 'qwerty')
        self.assertEqual(x.del_property('long_name'), 'qwerty')
        self.assertIsNone(x.get_property('long_name', None))
        self.assertIsNone(x.del_property('long_name', None))

    def test_FieldAncillary_insert_dimension(self):
        f = cfdm.read(self.filename)[0]
        d = f.dimension_coordinates('grid_longitude').value()
        x = cfdm.FieldAncillary(source=d)

        self.assertEqual(x.shape, (9,))

        y = x.insert_dimension(0)
        self.assertEqual(y.shape, (1, 9))

        x.insert_dimension(-1, inplace=True)
        self.assertEqual(x.shape, (9, 1))

    def test_FieldAncillary_transpose(self):
        f = cfdm.read(self.filename)[0]
        a = f.auxiliary_coordinates('longitude').value()
        x = cfdm.FieldAncillary(source=a)

        self.assertEqual(x.shape, (9, 10))

        y = x.transpose()
        self.assertEqual(y.shape, (10, 9))

        x.transpose([1, 0], inplace=True)
        self.assertEqual(x.shape, (10, 9))

    def test_FieldAncillary_squeeze(self):
        f = cfdm.read(self.filename)[0]
        a = f.auxiliary_coordinates('longitude').value()
        x = cfdm.FieldAncillary(source=a)

        x.insert_dimension(1, inplace=True)
        x.insert_dimension(0, inplace=True)

        self.assertEqual(x.shape, (1, 9, 1, 10))

        y = x.squeeze()
        self.assertEqual(y.shape, (9, 10))

        x.squeeze(2, inplace=True)
        self.assertEqual(x.shape, (1, 9, 10))

# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
