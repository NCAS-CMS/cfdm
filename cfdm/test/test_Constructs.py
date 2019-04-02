from __future__ import print_function

import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class ConstructsTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={!r}'.format(f))
        self.f = f[0]

        self.test_only = []
    #--- End: def

    def test_Constructs__repr__str__dump(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        c = f.constructs
        _ = repr(c)
        _ = str(c)
    #--- End: def

    def test_Constructs_key_items_value(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        for key, value in f.constructs.items():
            x = f.constructs.filter_by_key(key)
            self.assertTrue(x.key() == key)
            self.assertTrue(x.value().equals(value))
    #--- End: def


    def test_Constructs_copy_shallow_copy(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        c = self.f.constructs

        d = c.copy()
        self.assertTrue(c.equals(d, verbose=True))
        self.assertTrue(d.equals(c, verbose=True))

        d = c.shallow_copy()
        self.assertTrue(c.equals(d, verbose=True))
        self.assertTrue(d.equals(c, verbose=True))
    #--- End: def

    def test_Constructs_FILTER(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        c = self.f.constructs

        self.assertTrue(len(c) == 20)
        self.assertTrue(len(c.filter_by_identity()) == 20)
        self.assertTrue(len(c.filter_by_axis())     == 13)
        self.assertTrue(len(c.filter_by_key())      == 20)
        self.assertTrue(len(c.filter_by_data())     == 13)
        self.assertTrue(len(c.filter_by_property()) ==  9)
        self.assertTrue(len(c.filter_by_type())     == 20)
        self.assertTrue(len(c.filter_by_method())   ==  2)
        self.assertTrue(len(c.filter_by_measure())  ==  1)
        self.assertTrue(len(c.filter_by_ncvar())    == 14)
        self.assertTrue(len(c.filter_by_ncdim())    ==  3)

        self.assertTrue(len(c.filter_by_identity('qwerty')) == 0)
        self.assertTrue(len(c.filter_by_key('qwerty'))      == 0)
        self.assertTrue(len(c.filter_by_type('qwerty'))     == 0)
        self.assertTrue(len(c.filter_by_method('qwerty'))   == 0)
        self.assertTrue(len(c.filter_by_measure('qwerty'))  == 0)
        self.assertTrue(len(c.filter_by_ncvar('qwerty'))    == 0)
        self.assertTrue(len(c.filter_by_ncdim('qwerty'))    == 0)

        self.assertTrue(len(c.filter_by_identity('latitude'))        == 1)
        self.assertTrue(len(c.filter_by_key('dimensioncoordinate1')) == 1)
        self.assertTrue(len(c.filter_by_type('cell_measure'))        == 1)
        self.assertTrue(len(c.filter_by_method('mean'))              == 1)
        self.assertTrue(len(c.filter_by_measure('area'))             == 1)
        self.assertTrue(len(c.filter_by_ncvar('areacella'))          == 1)
        self.assertTrue(len(c.filter_by_ncdim('grid_longitude'))     == 1)

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
        for mode in ([], ['and'], ['or']):
            for kwargs in ({'qwerty': True},
                           {'domainaxis0': True},
                           {'domainaxis0': True, 'domainaxis1': True},
                           {'domainaxis0': True, 'domainaxis1': True, 'domainaxis2': True},
                           {'domainaxis0': False},
                           {'domainaxis0': False, 'domainaxis1': True},
                           {'domainaxis0': False, 'domainaxis1': True, 'domainaxis2': True},
            ):
                d = c.filter_by_axis(*mode, **kwargs)
                e = d.inverse_filter()
                self.assertTrue(len(e) == len(c) - len(d))

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

        # Unfilter
        self.assertTrue(e.unfilter(1).equals(d, verbose=True))        
        self.assertTrue(e.unfilter(1).unfilter().equals(c, verbose=True))
        self.assertTrue(d.unfilter(1).equals(c, verbose=True))        
        self.assertTrue(c.unfilter(1).equals(c, verbose=True))
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
