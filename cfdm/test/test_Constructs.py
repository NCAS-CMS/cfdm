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

        f = self.f.copy()

        for key, value in f.constructs.items():
            x = f.constructs.filter_by_key(key)
            self.assertTrue(x.key() == key)
            self.assertTrue(x.value().equals(value))
    #--- End: def

    def test_Constructs_FILTER(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

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

#        # property
#        for mode in ([], ['and'], ['or']):
#            for kwargs in ({'qwerty': 34},
#                           {'standard_name': 'surface_altitude'}):                
#                d = c.filter_by_property(*mode, **kwargs)
#                e = d.inverse_filter()
#                self.assertTrue(c.equals(e, verbose=True), repr(d))
#                self.assertTrue(e.equals(c, verbose=True), repr(d))
#            
#        # axis
#        for mode in ([], ['and'], ['or']):
#            for kwargs in ({'qwerty': True},
#                           {'domainaxis0': True}):
#                d = c.filter_by_axis(*mode, **kwargs)
#                _ = d.filters_applied()
#                _ = d.copy()
#                _ = d.shallow_copy()
#                e = d.inverse_filter()
#                self.assertTrue(c.equals(e, verbose=True), repr(d))            
#                self.assertTrue(e.equals(c, verbose=True), repr(d))            
#    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment())
    print('')
    unittest.main(verbosity=2)
