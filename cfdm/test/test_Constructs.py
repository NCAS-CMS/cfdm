from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm


class ConstructsTest(unittest.TestCase):
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
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []


    def test_Constructs__repr__str__dump(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        c = f.constructs
        _ = repr(c)
        _ = str(c)


    def test_Constructs_key_items_value(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for key, value in f.constructs.items():
            x = f.constructs.filter_by_key(key)
            self.assertTrue(x.key() == key)
            self.assertTrue(x.value().equals(value))


    def test_Constructs_copy_shallow_copy(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        c = self.f.constructs

        d = c.copy()
        self.assertTrue(c.equals(d, verbose=3))
        self.assertTrue(d.equals(c, verbose=3))

        d = c.shallow_copy()
        self.assertTrue(c.equals(d, verbose=3))
        self.assertTrue(d.equals(c, verbose=3))


    def test_Constructs_FILTER(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        c = self.f.constructs

        self.assertTrue(len(c) == 20)
        self.assertTrue(len(c.filter_by_identity()) == 20)
#        self.assertTrue(len(c.filter_by_axis())     == 13, str(c.filter_by_axis())) #x
        self.assertTrue(len(c.filter_by_axis())     == 13, str(c.filter_by_axis()))
        self.assertTrue(len(c.filter_by_key())      == 20)
        self.assertTrue(len(c.filter_by_data())     == 13)
        self.assertTrue(len(c.filter_by_property()) == 13, str(c.filter_by_property()))
        self.assertTrue(len(c.filter_by_type())     == 20)
        self.assertTrue(len(c.filter_by_method())   ==  2)
        self.assertTrue(len(c.filter_by_measure())  ==  1)
        self.assertTrue(len(c.filter_by_ncvar())    == 15, str(c.filter_by_ncvar()))
        self.assertTrue(len(c.filter_by_ncdim())    ==  3)

        self.assertTrue(len(c.filter_by_identity('qwerty')) == 0)
        self.assertTrue(len(c.filter_by_key('qwerty'))      == 0)
        self.assertTrue(len(c.filter_by_type('qwerty'))     == 0)
        self.assertTrue(len(c.filter_by_method('qwerty'))   == 0)
        self.assertTrue(len(c.filter_by_measure('qwerty'))  == 0)
        self.assertTrue(len(c.filter_by_ncvar('qwerty'))    == 0)
        self.assertTrue(len(c.filter_by_ncdim('qwerty'))    == 0)
        self.assertTrue(len(c.filter_by_size(-1))           == 0)

        self.assertTrue(len(c.filter_by_identity('latitude'))        == 1)
        self.assertTrue(len(c.filter_by_key('dimensioncoordinate1')) == 1)
        self.assertTrue(len(c.filter_by_type('cell_measure'))        == 1)
        self.assertTrue(len(c.filter_by_method('mean'))              == 1)
        self.assertTrue(len(c.filter_by_measure('area'))             == 1)
        self.assertTrue(len(c.filter_by_ncvar('areacella'))          == 1)
        self.assertTrue(len(c.filter_by_ncdim('grid_longitude'))     == 1)
        self.assertTrue(len(c.filter_by_size(9))                     == 1)

        constructs = c.filter_by_type('auxiliary_coordinate',
                                      'cell_measure',
                                      'cell_method',
                                      'coordinate_reference',
                                      'dimension_coordinate',
                                      'domain_ancillary',
                                      'domain_axis',
                                      'field_ancillary')
        n = 20
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))

        constructs = c.filter_by_type('auxiliary_coordinate')
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.AuxiliaryCoordinate)

        constructs = c.filter_by_type('cell_measure')
        n = 1
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMeasure)

        constructs = c.filter_by_size(9, 10)
        n = 2
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

        constructs = c.filter_by_type('cell_method')
        n = 2
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMethod)

        constructs = c.filter_by_type('dimension_coordinate')
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DimensionCoordinate)

        constructs = c.filter_by_type('coordinate_reference')
        n = 2
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CoordinateReference)

        constructs = c.filter_by_type('domain_ancillary')
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = c.filter_by_type('field_ancillary')
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.FieldAncillary)

        constructs = c.filter_by_type('domain_axis')
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

        constructs = c.filter_by_type(*['domain_ancillary'])
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = c.filter_by_type(*['domain_axis'])
        n =  3
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

        constructs = c.filter_by_type('domain_ancillary', 'domain_axis')
        n = 6
        self.assertTrue(len(constructs) == n,
                        'Got {} constructs, expected {}'.format(len(constructs), n))

        # Property
        for mode in ([], ['and'], ['or']):
            for kwargs in ({'qwerty': 34},
                           {'standard_name': 'surface_altitude'},
                           {'standard_name': 'surface_altitude', 'units': 'm'},
                           {'standard_name': 'surface_altitude', 'units': 'degrees'},
                           {'standard_name': 'surface_altitude', 'units': 'qwerty'},
            ):
                d = c.filter_by_property(*mode, **kwargs)
                e = d.inverse_filter()
                self.assertTrue(len(e) == len(c) - len(d))

        # Axis
#        for mode in ([], ['and'], ['or'], ['exact'], ['subset'], ['superset']):
        for mode in ('and', 'or', 'exact', 'subset'):
            for args in (['qwerty'],
                         ['domainaxis0'],
                         ['domainaxis0', 'domainaxis1'],
                         ['domainaxis0', 'domainaxis1', 'domainaxis2']):
#                           {'domainaxis0': False},
#                           {'domainaxis0': False, 'domainaxis1': True},
#                           {'domainaxis0': False, 'domainaxis1': True, 'domainaxis2': True},
#                d = c.filter_by_axis(*mode, **kwargs) #x
                d = c.filter_by_axis(mode, *args)
                e = d.inverse_filter()
                self.assertTrue(len(e) == len(c) - len(d))
        #--- End: for

        # Inverse filter, filters applied
        self.assertTrue(len(c.filters_applied()) == 0)
        ci = c.inverse_filter()
        self.assertTrue(len(ci) == 0)
        self.assertTrue(len(ci) == len(c) - len(c))

        d = c.filter_by_type('dimension_coordinate', 'auxiliary_coordinate')
        self.assertTrue(len(d.filters_applied()) == 1)
        di = d.inverse_filter()
        self.assertTrue(len(di) == len(c) - len(d))

        e = d.filter_by_property(units='degrees')
        self.assertTrue(len(e.filters_applied()) == 2)
        ei = e.inverse_filter(1)
        self.assertTrue(len(e.filters_applied()) == 2)
        self.assertTrue(len(ei) == len(d) - len(e))

        d2 = c.filter_by_type('auxiliary_coordinate')
        e2 = d2.filter_by_naxes(1)
        f2 = e2.inverse_filter(1)
        g2 = f2.inverse_filter(1)
        h2 = g2.inverse_filter(1)
        self.assertTrue(g2.equals(e2, verbose=3))
        self.assertTrue(h2.equals(f2, verbose=3))

        # Unfilter
        self.assertTrue(e.unfilter(1).equals(d, verbose=3))
        self.assertTrue(e.unfilter(1).unfilter().equals(c, verbose=3))
        self.assertTrue(d.unfilter(1).equals(c, verbose=3))
        self.assertTrue(c.unfilter(1).equals(c, verbose=3))


#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
