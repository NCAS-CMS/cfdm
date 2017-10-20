import datetime
import inspect
import os
import sys
import unittest

import cfdm

class CellMethodsTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    strings = ('t: mean',
               'time: point',
               'time: maximum',
               'time: sum',
               'lon: maximum time: mean',
               'time: mean lon: maximum',
               'lat: lon: standard_deviation',
               'lon: standard_deviation lat: standard_deviation',
               'time: standard_deviation (interval: 1 day)',
               'area: mean',
               'lon: lat: mean',
               'time: variance (interval: 1 hr comment: sampled instantaneously)',
               'time: mean',
               'time: mean time: maximum',
               'time: mean within years time: maximum over years',
               'time: mean within days time: maximum within years time: variance over years',
               'time: standard_deviation (interval: 1 day)',
               'time: standard_deviation (interval: 1 year)',
               'time: standard_deviation (interval: 30 year)',
               'time: standard_deviation (interval: 1.0 year)',
               'time: standard_deviation (interval: 30.0 year)',
               'lat: lon: standard_deviation (interval: 10 km)',
               'lat: lon: standard_deviation (interval: 10 km interval: 10 km)',
               'lat: lon: standard_deviation (interval: 0.1 degree_N interval: 0.2 degree_E)', 
               'lat: lon: standard_deviation (interval: 0.123 degree_N interval: 0.234 degree_E)',
               'time: variance (interval: 1 hr comment: sampled instantaneously)',
               'area: mean where land',
               'area: mean where land_sea',
               'area: mean where sea_ice over sea',
               'area: mean where sea_ice over sea',
               'time: minimum within years time: mean over years',
               'time: sum within years time: mean over years',
               'time: mean within days time: mean over days',
               'time: minimum within days time: sum over days',
               'time: minimum within days time: maximum over days',
               'time: mean within days',
               'time: sum within days time: maximum over days',
           )

    test_only = []
#    test_only = ['test_CellMethods___str__']
#    test_only = ['test_CellMethods_equals']
#    test_only = ['test_CellMethods_equivalent']
#    test_only = ['test_CellMethods_get_set_delete']

    def test_CellMethods___str__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for s in self.strings:
            print s
            cm = cfdm.CellMethods(s)           
            self.assertTrue(s == str(cm), '{!r} != {!r}'.format(s, str(cm)))
    #--- End: def

    def test_CellMethods_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for s in self.strings:
            cm0 = cfdm.CellMethods(s)
            cm1 = cfdm.CellMethods(s)
            self.assertTrue(cm0.equals(cm1, traceback=True),
                            '%r != %r' % (cm0, cm1))
        #--- End: for
    #--- End: def

    def test_CellMethods_equivalent(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for s in self.strings:
            cm0 = cfdm.CellMethods(s)
            cm1 = cfdm.CellMethods(s)
            self.assertTrue(cm0.equivalent(cm1),
                            '{!r} not equivalent to {!r}'.format(cm0, cm1))
        #--- End: for

        # Intervals
        for s0, s1 in (
                ['lat: lon: mean (interval: 10 km)',
                 'lat: lon: mean (interval: 10 km)'],
                ['lat: lon: mean (interval: 10 km)',
                 'lat: lon: mean (interval: 10 km interval: 10 km)'],
                ['lat: lon: mean (interval: 10 km interval: 10 km)',
                 'lat: lon: mean (interval: 10 km interval: 10 km)'],
                ['lat: lon: mean (interval: 20 km interval: 10 km)',
                 'lat: lon: mean (interval: 20 km interval: 10 km)'],  
                ['lat: lon: mean (interval: 20 km interval: 10 km)',
                 'lat: lon: mean (interval: 20000 m interval: 10000 m)'],  

                ['lat: lon: mean (interval: 10 km)',
                 'lon: lat: mean (interval: 10 km)'],
                ['lat: lon: mean (interval: 10 km)',
                 'lon: lat: mean (interval: 10 km interval: 10 km)'],
                ['lat: lon: mean (interval: 10 km interval: 10 km)',
                 'lon: lat: mean (interval: 10 km interval: 10 km)'],
                ['lat: lon: mean (interval: 20 km interval: 10 km)',
                 'lon: lat: mean (interval: 10 km interval: 20 km)'],  
                ['lat: lon: mean (interval: 20 km interval: 10 km)',
                 'lon: lat: mean (interval: 10000 m interval: 20000 m)'],  
        ):
            cm0 = cfdm.CellMethods(s0)
            cm1 = cfdm.CellMethods(s1)

            self.assertTrue(cm0.equivalent(cm1, traceback=True),
                            '{0!r} not equivalent to {1!r}'.format(cm0, cm1))
        #--- End: for
    #--- End: def

    def test_CellMethods_get_set_delete(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        c = cfdm.CellMethods('time: minimum within days time: sum over years')

        self.assertTrue(c[0].__class__.__name__ == 'CellMethod')
        self.assertTrue(c[1].__class__.__name__ == 'CellMethod')
        self.assertTrue(c[-1].__class__.__name__ == 'CellMethod')
        self.assertTrue(c[-2].__class__.__name__ == 'CellMethod')

        self.assertTrue(c[0:1].__class__.__name__ == 'CellMethods')
        self.assertTrue(c[0:-1].__class__.__name__ == 'CellMethods')
        self.assertTrue(c[0:2].__class__.__name__ == 'CellMethods')
        self.assertTrue(c[0:99].__class__.__name__ == 'CellMethods')
        self.assertTrue(c[0:0].__class__.__name__ == 'CellMethods')

        self.assertTrue(len(c[0:1]) == 1)
        self.assertTrue(len(c[0:-1]) == 1)
        self.assertTrue(len(c[0:2]) == 2)
        self.assertTrue(len(c[0:-2]) == 0)
        self.assertTrue(len(c[0:99]) == 2)
        self.assertTrue(len(c[0:0]) == 0)

        self.assertTrue(c.within == ('days', None))
        self.assertTrue(c.where == (None, None))
        self.assertTrue(c.over == (None, 'years'))
        self.assertTrue(c.method == ('minimum', 'sum'))
        self.assertTrue(c.axes == (('time',), ('time',)))
    #--- End: def

#--- End: class


if __name__ == "__main__":
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print''
    unittest.main(verbosity=2)
