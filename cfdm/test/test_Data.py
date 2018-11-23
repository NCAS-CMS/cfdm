from __future__ import print_function
from builtins import range
import datetime
import inspect
import itertools
from operator import mul
import os
import sys
import time
import unittest


import numpy

import cfdm

class DataTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    test_only = []
#    test_only = ['NOTHING!!!!!']
#    test_only = ['test_Data__asdatetime__asreftime__isdatetime']
#    test_only = ['test_Data___setitem__']
#    test_only = ['test_Data_ceil', 'test_Data_floor', 'test_Data_trunc', 'test_Data_rint']
#    test_only = ['test_Data_array', 'test_Data_dtarray']
#    test_only = ['test_dumpd_loadd']
#    test_only = ['test_Data_BINARY_AND_UNARY_OPERATORS']

    def test_Data___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
        
    def test_Data___setitem__(self):        
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.arange(3000).reshape(50, 60)

        d = cfdm.Data(a.filled(), units='m')
        
        for n, (j, i) in enumerate(((34, 23), (0, 0), (-1, -1),
                                    (slice(40, 50), slice(58, 60)),
                                    (Ellipsis, slice(None)),
                                    (slice(None), Ellipsis),
                                  )):
            n = -n-1
            for dvalue, avalue in ((n, n), (cfdm.masked, numpy.ma.masked), (n, n)):
                message = "cfdm.Data[{}, {}]={}={} failed".format(j, i, dvalue, avalue)
                d[j, i] = dvalue
                a[j, i] = avalue
                x = d.get_array()
                self.assertTrue((x == a).all() in (True, numpy.ma.masked), message)
                m = numpy.ma.getmaskarray(x)
                self.assertTrue((m == numpy.ma.getmaskarray(a)).all(), 
                                'd.mask.array='+repr(m)+'\nnumpy.ma.getmaskarray(a)='+repr(numpy.ma.getmaskarray(a)))
        #--- End: for
    
        a = numpy.ma.arange(3000).reshape(50, 60)
        
        d = cfdm.Data(a.filled(), 'm')
        
        (j, i) = (slice(0, 2), slice(0, 3))
        array = numpy.array([[1, 2, 6],[3, 4, 5]])*-1
        
        for dvalue in (array,
                       numpy.ma.masked_where(array < -2, array),
                       array):
            message = 'cfdm.Data[%s, %s]=%s failed' % (j, i, dvalue)
            d[j, i] = dvalue
            a[j, i] = dvalue
            x = d.get_array()
            self.assertTrue((x == a).all() in (True, numpy.ma.masked), message)
            m = numpy.ma.getmaskarray(x)
            self.assertTrue((m == numpy.ma.getmaskarray(a)).all(), message)
        #--- End: for
        
        # Scalar numeric array
        d = cfdm.Data(9, units='km')
        d[...] = cfdm.masked
        a = d.get_array()
        self.assertTrue(a.shape == ())
        self.assertTrue(a[()] is numpy.ma.masked)
    #--- End: def

    def test_Data_get_array(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Scalar numeric array
        d = cfdm.Data(9, units='km')
        a = d.get_array()
        self.assertTrue(a.shape == ())
        self.assertTrue(a == numpy.array(9))
        d[...] = cfdm.masked
        a = d.get_array()
        self.assertTrue(a.shape == ())
        self.assertTrue(a[()] is numpy.ma.masked)

        # Non-scalar numeric array
        b = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(b, 'km')
        a = d.get_array()
        a[0,0,0,0] = -999
        a2 = d.get_array()
        self.assertTrue(a2[0,0,0,0] == 0)
        self.assertTrue(a2.shape == b.shape)
        self.assertTrue((a2 == b).all())
        self.assertFalse((a2 == a).all())
    #--- End: def

    def test_Data_get_dtarray(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.Data(11292.5, units='days since 1970-1-1')
        dt = d.get_dtarray()[()]
        self.assertTrue(dt == datetime.datetime(2000, 12, 1, 12, 0))
    #--- End: def

    def test_Data_transpose(self):        
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(a.copy())
        
        for indices in (list(range(a.ndim)), list(range(-a.ndim, 0))):
            for axes in itertools.permutations(indices):
                a = numpy.transpose(a, axes)
                d = d.transpose(axes)
                message = 'cfdm.Data.transpose({}) failed: d.shape={}, a.shape={}'.format(
                    axes, d.shape, a.shape)
                self.assertTrue(d.shape == a.shape, message)
                self.assertTrue((d.get_array() == a).all(), message)
            #--- End: for
        #--- End: for
    #--- End: def
        
    def test_Data_unique(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
            
        d = cfdm.Data([[4, 2, 1], [1, 2, 3]], units='metre')
        u = d.unique()
        self.assertTrue(u.shape == (4,))
        self.assertTrue((u.get_array() == cfdm.Data([1, 2, 3, 4], 'metre').get_array()).all())

        d[1, -1] = cfdm.masked
        u = d.unique()
        self.assertTrue(u.shape == (3,))        
        self.assertTrue((u.get_array() == cfdm.Data([1, 2, 4], 'metre').get_array()).all())
    #--- End: def

#--- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
