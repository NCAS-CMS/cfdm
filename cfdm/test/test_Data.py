from __future__ import print_function
from builtins import range

import copy
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
#    test_only = ['test_Data__setitem__']
#    test_only = ['test_Data_ceil', 'test_Data_floor', 'test_Data_trunc', 'test_Data_rint']
#    test_only = ['test_Data_array', 'test_Data_datetime_array']
#    test_only = ['test_dumpd_loadd']
#    test_only = ['test_Data_BINARY_AND_UNARY_OPERATORS']

    def test_Data__repr__str(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for d in [cfdm.Data(9, units='km'),
                  cfdm.Data([9], units='km'),
                  cfdm.Data([[9]], units='km'),
                  cfdm.Data([8, 9], units='km'),
                  cfdm.Data([[8, 9]], units='km'),
                  cfdm.Data([7, 8, 9], units='km'),
                  cfdm.Data([[7, 8, 9]], units='km'),
                  cfdm.Data([6, 7, 8, 9], units='km'),
                  cfdm.Data([[6, 7, 8, 9]], units='km'),
                  cfdm.Data([[6, 7], [8, 9]], units='km'),
                  cfdm.Data([[6, 7, 8, 9], [6, 7, 8, 9]], units='km'),
        ]:
            _ = repr(d)
            _ = str(d)
    #--- End: def

#    def test_Data__getitem__(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
                

    def test_Data__setitem__(self):        
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
                x = d.array
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
            x = d.array
            self.assertTrue((x == a).all() in (True, numpy.ma.masked), message)
            m = numpy.ma.getmaskarray(x)
            self.assertTrue((m == numpy.ma.getmaskarray(a)).all(), message)
        #--- End: for
        
        # Scalar numeric array
        d = cfdm.Data(9, units='km')
        d[...] = cfdm.masked
        a = d.array
        self.assertTrue(a.shape == ())
        self.assertTrue(a[()] is numpy.ma.masked)
    #--- End: def

#    def test_Data_astype(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        a = numpy.array([1.5, 2, 2.5], dtype=float)       
#        d = cfdm.Data(a)
#        
#        self.assertTrue(d.dtype == numpy.dtype(float))
#        self.assertTrue(d.array.dtype == numpy.dtype(float))
#        self.assertTrue((d.array == a).all())
#
#        d.astype('int32')
#        self.assertTrue(d.dtype == numpy.dtype('int32'))
#        self.assertTrue(d.array.dtype == numpy.dtype('int32'))
#        self.assertTrue((d.array == [1, 2, 2]).all())
#
#        d = cfdm.Data(a)
#        try:
#            d.astype(numpy.dtype(int, casting='safe'))
#            self.assertTrue(False)
#        except TypeError:
#            pass
#    #--- End: def

    def test_Data_array(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # ------------------------------------------------------------
        # Numpy array interface (__array__)
        # ------------------------------------------------------------
        a = numpy.arange(12, dtype='int32').reshape(3, 4)

        d = cfdm.Data(a, units='km')

        b = numpy.array(d)

        self.assertTrue(b.dtype == numpy.dtype('int32'))
        self.assertTrue(a.shape == b.shape)
        self.assertTrue((a == b).all())        

        b = numpy.array(d, dtype='float32')

        self.assertTrue(b.dtype == numpy.dtype('float32'))
        self.assertTrue(a.shape == b.shape)
        self.assertTrue((a == b).all())

        
        # Scalar numeric array
        d = cfdm.Data(9, units='km')
        a = d.array
        self.assertTrue(a.shape == ())
        self.assertTrue(a == numpy.array(9))
        d[...] = cfdm.masked
        a = d.array
        self.assertTrue(a.shape == ())
        self.assertTrue(a[()] is numpy.ma.masked)

        # Non-scalar numeric array
        b = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(b, 'km')
        a = d.array
        a[0,0,0,0] = -999
        a2 = d.array
        self.assertTrue(a2[0,0,0,0] == 0)
        self.assertTrue(a2.shape == b.shape)
        self.assertTrue((a2 == b).all())
        self.assertFalse((a2 == a).all())
    #--- End: def

    def test_Data_datetime_array(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.Data(11292.5, units='days since 1970-1-1')
        dt = d.datetime_array[()]
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
                self.assertTrue((d.array == a).all(), message)
            #--- End: for
        #--- End: for
    #--- End: def
        
    def test_Data_unique(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
            
        d = cfdm.Data([[4, 2, 1], [1, 2, 3]], units='metre')
        u = d.unique()
        self.assertTrue(u.shape == (4,))
        self.assertTrue((u.array == cfdm.Data([1, 2, 3, 4], 'metre').array).all())
        

        d[1, -1] = cfdm.masked
        u = d.unique()
        self.assertTrue(u.shape == (3,))        
        self.assertTrue((u.array == cfdm.Data([1, 2, 4], 'metre').array).all())
    #--- End: def

    def test_Data_equals(self):        
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.arange(10*15*19).reshape(10, 1, 15, 19)
        a[0, 0, 2, 3] = numpy.ma.masked
        
        d = cfdm.Data(a, units='days since 2000-2-2', calendar='noleap')
        e = copy.deepcopy(d)

        self.assertTrue(d.equals(d, verbose=True))
        self.assertTrue(d.equals(e, verbose=True))
        self.assertTrue(e.equals(d, verbose=True))    
    #--- End: def
        
    def test_Data_max_min_sum_squeeze(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        
        a = numpy.ma.arange(10*15*19).reshape(10, 1, 15, 19)
        a[0, 0, 0, 0] = numpy.ma.masked
        a[-1, -1, -1, -1] = numpy.ma.masked
        a[5, -1, 6, 10] = numpy.ma.masked
        d = cfdm.Data(a)

        b = a.max()
        x = d.max().squeeze()
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=(0, 3))
        x = d.max(axes=[0, 3]).squeeze([0, 3])
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min()
        x = d.min().squeeze()
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min(axis=(0, 3))
        x = d.min(axes=[0, 3]).squeeze([0, 3])
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all(), (x.shape, b.shape))

        b = a.sum()
        x = d.sum().squeeze()
        self.assertTrue(x.shape== b.shape)
        self.assertTrue((x.array == b).all())

        b = a.sum(axis=(0, 3))
        x = d.sum(axes=[0, 3]).squeeze([0, 3])
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all(), (x.shape, b.shape))
    #--- End: def

#--- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
