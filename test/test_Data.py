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
#    test_only = ['test_Data_array', 'test_Data_varray', 'test_Data_dtarray']
#    test_only = ['test_dumpd_loadd']
#    test_only = ['test_Data_BINARY_AND_UNARY_OPERATORS']

    def test_Data___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
        
    def test_Data___setitem__(self):        
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for hardmask in (False, True):
            a = numpy.ma.arange(3000).reshape(50, 60)
            if hardmask:
                a.harden_mask()
            else:
                a.soften_mask()
                    
            d = cfdm.Data(a.filled(), 'm')
            d.hardmask = hardmask
            
            for n, (j, i) in enumerate(((34, 23), (0, 0), (-1, -1),
                                        (slice(40, 50), slice(58, 60)),
                                        (Ellipsis, slice(None)),
                                        (slice(None), Ellipsis),
            )):
                n = -n-1
                for dvalue, avalue in ((n, n), (cfdm.masked, numpy.ma.masked), (n, n)):
                    message = "hardmask={}, cfdm.Data[{}, {}]]={}={} failed".format(hardmask, j, i, dvalue, avalue)
                    d[j, i] = dvalue
                    a[j, i] = avalue
                    self.assertTrue((d.array == a).all() in (True, numpy.ma.masked), message)
                    self.assertTrue((d.mask.array == numpy.ma.getmaskarray(a)).all(), 
                                        'd.mask.array='+repr(d.mask.array)+'\nnumpy.ma.getmaskarray(a)='+repr(numpy.ma.getmaskarray(a)))
            #--- End: for
    
            a = numpy.ma.arange(3000).reshape(50, 60)
            if hardmask:
                a.harden_mask()
            else:
                a.soften_mask()
    
            d = cfdm.Data(a.filled(), 'm')
            d.hardmask = hardmask
            
            (j, i) = (slice(0, 2), slice(0, 3))
            array = numpy.array([[1, 2, 6],[3, 4, 5]])*-1
            for dvalue in (array,
                           numpy.ma.masked_where(array < -2, array),
                           array):
                message = 'cfdm.Data[%s, %s]=%s failed' % (j, i, dvalue)
                d[j, i] = dvalue
                a[j, i] = dvalue
                self.assertTrue((d.array == a).all() in (True, numpy.ma.masked), message)
                self.assertTrue((d.mask.array == numpy.ma.getmaskarray(a)).all(), message)
            #--- End: for
        #--- End: for
    #--- End: def

    def test_Data_array(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Scalar numeric array
        d = cfdm.Data(9, 'km')
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

        d = cfdm.Data([['2000-12-3 12:00']], 'days since 2000-12-01', dt=True)
        a = d.array
        self.assertTrue((a == numpy.array([[2.5]])).all())
    #--- End: def

    def test_Data_dtarray(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Scalar array
        for d, x in zip([cfdm.Data(11292.5, 'days since 1970-1-1'),
                         cfdm.Data('2000-12-1 12:00', dt=True)],
                        [11292.5, 0.5]):
            a = d.dtarray
            self.assertTrue(a.shape == ())
            self.assertTrue(a == numpy.array(cfdm.dt('2000-12-1 12:00')))

            a = d.array
            self.assertTrue(a.shape == ())
            self.assertTrue(a == x, repr(a)+' '+repr(x))

            a = d.dtarray
            a = d.array
            self.assertTrue(a.shape == ())
            self.assertTrue(a == x, repr(a)+' '+repr(x))

        # Non-scalar array
        for d, x in zip([cfdm.Data([[11292.5, 11293.5]], 'days since 1970-1-1'),
                         cfdm.Data([['2000-12-1 12:00', '2000-12-2 12:00']], dt=True)],
                        ([[11292.5, 11293.5]],
                         [[0.5, 1.5]])):
            a = d.dtarray
            a = d.array
            self.assertTrue((a == x).all(), repr(a)+' '+repr(x))

            a = d.dtarray
            a = d.array
            self.assertTrue((a == x).all(), repr(a)+' '+repr(x))
            
            a = d.dtarray
            self.assertTrue((a == numpy.array([[cfdm.dt('2000-12-1 12:00'),
                                                cfdm.dt('2000-12-2 12:00')]])).all(),
                            repr(a)+' '+repr(x))
    #--- End: def

#    def test_Data__asdatetime__asreftime__isdatetime(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        d = cfdm.Data([[1.93, 5.17]], 'days since 2000-12-29')
#        self.assertTrue(d.dtype == numpy.dtype(float))
#        self.assertFalse(d._isdatetime())
#        d._asreftime(copy=False)
#        self.assertTrue(d.dtype == numpy.dtype(float))
#        self.assertFalse(d._isdatetime())
#        d._asdatetime(copy=False)
#        self.assertTrue(d.dtype == numpy.dtype(object))
#        self.assertTrue(d._isdatetime())
#        d._asdatetime(copy=False)
#        self.assertTrue(d.dtype == numpy.dtype(object))
#        self.assertTrue(d._isdatetime())
#        d._asreftime(copy=False)
#        self.assertTrue(d.dtype == numpy.dtype(float))
#        self.assertFalse(d._isdatetime())
#    #--- End: def

    def test_Data_datum(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
        
        d = cfdm.Data(5, 'metre')
        self.assertTrue(d.datum()   == 5)
        self.assertTrue(d.datum(0)  == 5)
        self.assertTrue(d.datum(-1) == 5)
        
        for d in [cfdm.Data([4, 5, 6, 1, 2, 3], 'metre'),
                  cfdm.Data([[4, 5, 6], [1, 2, 3]], 'metre')]:
            self.assertTrue(d.datum(0)  == 4)
            self.assertTrue(d.datum(-1) == 3)
            for index in d.ndindex():
                self.assertTrue(d.datum(index)  == d.array[index].item())
                self.assertTrue(d.datum(*index) == d.array[index].item())
        #--- End: for
            
        d = cfdm.Data(5, 'metre')
        d[()] = cfdm.masked
        self.assertTrue(d.datum()   is cfdm.masked)
        self.assertTrue(d.datum(0)  is cfdm.masked)
        self.assertTrue(d.datum(-1) is cfdm.masked)
        
        d = cfdm.Data([[5]], 'metre')
        d[0, 0] = cfdm.masked
        self.assertTrue(d.datum()        is cfdm.masked)
        self.assertTrue(d.datum(0)       is cfdm.masked)
        self.assertTrue(d.datum(-1)      is cfdm.masked)
        self.assertTrue(d.datum(0, 0)    is cfdm.masked)
        self.assertTrue(d.datum(-1, 0)   is cfdm.masked)
        self.assertTrue(d.datum([0, 0])  is cfdm.masked)
        self.assertTrue(d.datum([0, -1]) is cfdm.masked)
        self.assertTrue(d.datum(-1, -1)  is cfdm.masked)
    #--- End: def

#    def test_Data_ndindex(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        for chunksize in self.chunk_sizes:   
#            cfdm.CHUNKSIZE(chunksize)          
#            for d in (cfdm.Data(5, 'metre'),
#                      cfdm.Data([4, 5, 6, 1, 2, 3], 'metre'),
#                      cfdm.Data([[4, 5, 6], [1, 2, 3]], 'metre')
#                      ):
#                for i, j in zip(d.ndindex(), numpy.ndindex(d.shape)):
#                    self.assertTrue(i == j)
#                #--- End: for
#            #--- End: for
#        #--- End: for
#
#        cfdm.CHUNKSIZE(self.original_chunksize)
#    #--- End: def
        
#    def test_Data_swapaxes(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        for chunksize in self.chunk_sizes:   
#            cfdm.CHUNKSIZE(chunksize)          
#            a = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
#            d = cfdm.Data(a.copy())
#     
#            for i in range(-a.ndim, a.ndim):
#                for j in range(-a.ndim, a.ndim):
#                    b = numpy.swapaxes(a.copy(), i, j)
#                    e = d.swapaxes(i, j)
#                    message = 'cfdm.Data.swapaxes({}, {}) failed'.format(i, j)
#                    self.assertTrue(b.shape == e.shape, message)
#                    self.assertTrue((b == e.array).all(), message)
#                #--- End: for
#            #--- End: for
#        #--- End: for
#        cfdm.CHUNKSIZE(self.original_chunksize)
#    #--- End: def
#                
    def test_Data_transpose(self):        
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(a.copy())
        
        for indices in (range(a.ndim), range(-a.ndim, 0)):
            for axes in itertools.permutations(indices):
                a = numpy.transpose(a, axes)
                d.transpose(axes, copy=False)
                message = 'cfdm.Data.transpose(%s) failed: d.shape=%s, a.shape=%s' % \
                          (axes, d.shape, a.shape)
                self.assertTrue(d.shape == a.shape, message)
                self.assertTrue((d.array == a).all(), message)
            #--- End: for
        #--- End: for
    #--- End: def
        
    def test_Data_unique(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
            
        d = cfdm.Data([[4, 2, 1], [1, 2, 3]], 'metre')
        u = d.unique()
        self.assertTrue(u.Units == d.Units)
        self.assertTrue(u.shape == (4,))
        self.assertTrue((u.array == cfdm.Data([1, 2, 3, 4], 'metre').array).all())

        d[1, -1] = cfdm.masked
        u = d.unique()
        self.assertTrue(u.Units == d.Units)
        self.assertTrue(u.shape == (3,))        
        self.assertTrue((u.array == cfdm.Data([1, 2, 4], 'metre').array).all())
    #--- End: def

    def test_Data_varray(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Scalar array
        d = cfdm.Data(9, 'km')
        d.hardmask = False
        a = d.varray
        self.assertTrue(a.shape == ())
        self.assertTrue(a == numpy.array(9))
        d[...] = cfdm.masked
        a = d.varray
        self.assertTrue(a.shape == ())
        self.assertTrue(a[()] is numpy.ma.masked)
        a[()] = 18
        self.assertTrue(a == numpy.array(18))

        b = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(b, 'km')
        e = d.copy()
        v = e.varray
        v[0,0,0,0] = -999
        v = e.varray
        self.assertTrue(v[0,0,0,0] == -999)
        self.assertTrue(v.shape == b.shape)
        self.assertFalse((v == b).all())
        v[0, 0, 0, 0] = 0
        self.assertTrue((v == b).all())
    #--- End: def

#    def test_Data_year_month_day_hour_minute_second(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#            
#        d = cfdm.Data([[1.901, 5.101]], 'days since 2000-12-29')
#        self.assertTrue(d.year.equals(cfdm.Data([[2000, 2001]])))
#        self.assertTrue(d.month.equals(cfdm.Data([[12, 1]])))
#        self.assertTrue(d.day.equals(cfdm.Data([[30, 3]])))
#        self.assertTrue(d.hour.equals(cfdm.Data([[21, 2]])))
#        self.assertTrue(d.minute.equals(cfdm.Data([[37, 25]])))
#        self.assertTrue(d.second.equals(cfdm.Data([[26, 26]])))
#
#        d = cfdm.Data([[1.901, 5.101]],
#                    cfdm.Units('days since 2000-12-29', '360_day'))
#        self.assertTrue(d.year.equals(cfdm.Data([[2000, 2001]])))
#        self.assertTrue(d.month.equals(cfdm.Data([[12, 1]])))
#        self.assertTrue(d.day.equals(cfdm.Data([[30, 4]])))
#        self.assertTrue(d.hour.equals(cfdm.Data([[21, 2]])))
#        self.assertTrue(d.minute.equals(cfdm.Data([[37, 25]])))
#        self.assertTrue(d.second.equals(cfdm.Data([[26, 26]])))
#        
#        cfdm.CHUNKSIZE(self.original_chunksize)   
#    #--- End: def
#
#    def test_Data_BINARY_AND_UNARY_OPERATORS(self):        
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        for chunksize in self.chunk_sizes:
#            cfdm.CHUNKSIZE(chunksize)          
#            array = numpy.arange(3*4*5).reshape(3, 4, 5) + 1
#            
#            arrays =  (numpy.arange(3*4*5).reshape(3, 4, 5) + 1.0,
#                       numpy.arange(3*4*5).reshape(3, 4, 5) + 1)
#
#            for a0 in arrays:
#                for a1 in arrays[::-1]:
#                    d = cfdm.Data(a0[(slice(None, None, -1),)*a0.ndim], 'metre')
#                    d.flip(copy=False)
#                    x = cfdm.Data(a1, 'metre')
#                    
#                    message = 'Failed in {!r}+{!r}'.format(d, x)
#                    self.assertTrue((d +  x).equals(cfdm.Data(a0 +  a1, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}*{!r}'.format(d, x)
#                    self.assertTrue((d *  x).equals(cfdm.Data(a0 *  a1, 'm2'), traceback=1), message)
#                    message = 'Failed in {!r}/{!r}'.format(d, x)
#                    self.assertTrue((d /  x).equals(cfdm.Data(a0 /  a1, '1' ), traceback=1), message)
#                    message = 'Failed in {!r}-{!r}'.format(d, x)
#                    self.assertTrue((d -  x).equals(cfdm.Data(a0 -  a1, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}//{!r}'.format(d, x)
#                    self.assertTrue((d // x).equals(cfdm.Data(a0 // a1, '1' ), traceback=1), message)
#
#                    message = 'Failed in {!r}.__truediv__//{!r}'.format(d, x)
#                    self.assertTrue(d.__truediv__(x).equals(cfdm.Data(array.__truediv__(array), '1'), traceback=1), message)
#
#                    message = 'Failed in {!r}__rtruediv__{!r}'.format(d, x)
#                    self.assertTrue(d.__rtruediv__(x).equals(cfdm.Data(array.__rtruediv__(array), '1'), traceback=1) , message)
#                    
#                    try:
#                        d ** x
#                    except:
#                        pass
#                    else:
#                        message = 'Failed in {!r}**{!r}'.format(d, x)
#                        self.assertTrue((d**x).all(), message)
#                #--- End: for                       
#            #--- End: for                       
#                      
#            for a0 in arrays:
#                d = cfdm.Data(a0, 'metre')
#                for x in (2, 2.0,):
#                    message = 'Failed in {!r}+{}'.format(d, x)
#                    self.assertTrue((d +  x).equals(cfdm.Data(a0 +  x, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}*{}'.format(d, x) 
#                    self.assertTrue((d *  x).equals(cfdm.Data(a0 *  x, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}/{}'.format(d, x) 
#                    self.assertTrue((d /  x).equals(cfdm.Data(a0 /  x, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}-{}'.format(d, x) 
#                    self.assertTrue((d -  x).equals(cfdm.Data(a0 -  x, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}//{}'.format(d, x)
#                    self.assertTrue((d // x).equals(cfdm.Data(a0 // x, 'm' ), traceback=1), message)
#                    message = 'Failed in {!r}**{}'.format(d, x)
#                    self.assertTrue((d ** x).equals(cfdm.Data(a0 ** x, 'm2'), traceback=1), message)
#                    message = 'Failed in {!r}.__truediv__{}'.format(d, x)
#                    self.assertTrue(d.__truediv__(x).equals(cfdm.Data(a0.__truediv__(x), 'm'), traceback=1), message)
#                    message = 'Failed in {!r}.__rtruediv__{}'.format(d, x)
#                    self.assertTrue(d.__rtruediv__(x).equals(cfdm.Data(a0.__rtruediv__(x), 'm-1'), traceback=1), message)
#                    
#                    message = 'Failed in {}+{!r}'.format(x, d)
#                    self.assertTrue((x +  d).equals(cfdm.Data(x +  a0, 'm'  ), traceback=1), message)
#                    message = 'Failed in {}*{!r}'.format(x, d)
#                    self.assertTrue((x *  d).equals(cfdm.Data(x *  a0, 'm'  ), traceback=1), message)
#                    message = 'Failed in {}/{!r}'.format(x, d)
#                    self.assertTrue((x /  d).equals(cfdm.Data(x /  a0, 'm-1'), traceback=1), message)
#                    message = 'Failed in {}-{!r}'.format(x, d)
#                    self.assertTrue((x -  d).equals(cfdm.Data(x -  a0, 'm'  ), traceback=1), message)
#                    message = 'Failed in {}//{!r}\n{!r}\n{!r}'.format(x, d, x//d, x//a0)
#                    self.assertTrue((x // d).equals(cfdm.Data(x // a0, 'm-1'), traceback=1), message)
#                    
#                    try:
#                        x ** d
#                    except:
#                        pass
#                    else:
#                        message = 'Failed in {}**{!r}'.format(x, d)
#                        self.assertTrue((x**d).all(), message)
#
##                    print 'START ====================', repr(d)
#                    a = a0.copy()                        
#                    try:
#                        a += x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
##                        print '0 ------'
#                        e += x
##                        print '1 ------'
#                        message = 'Failed in {!r}+={}'.format(d, x)
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1), message)
##                    print 'END ====================', repr(d)
#
#                    a = a0.copy()                        
#                    try:
#                        a *= x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e *= x
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1)), '%s*=%s' % (repr(d), x)
#
#                    a = a0.copy()                        
#                    try:
#                        a /= x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e /= x
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1)), '%s/=%s' % (repr(d), x)
#
#                    a = a0.copy()                        
#                    try:
#                        a -= x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e -= x
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1)), '%s-=%s' % (repr(d), x)
#
#                    a = a0.copy()                        
#                    try:
#                        a //= x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e //= x
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1)), '%s//=%s' % (repr(d), x)
#
#                    a = a0.copy()                        
#                    try:
#                        a **= x
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e **= x
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm2'), traceback=1)), '%s**=%s' % (repr(d), x)
#
#                    a = a0.copy()                        
#                    try:
#                        a.__itruediv__(x)
#                    except TypeError:
#                        pass
#                    else:
#                        e = d.copy()
#                        e.__itruediv__(x)
#                        self.assertTrue(e.equals(cfdm.Data(a, 'm'), traceback=1)), '%s.__itruediv__(%s)' % (d, x)
#                #--- End: for
#                
#                for x in (cfdm.Data(2, 'metre'), cfdm.Data(2.0, 'metre')):
#                    self.assertTrue((d +  x).equals(cfdm.Data(a0 +  x.datum(), 'm' ), traceback=1))
#                    self.assertTrue((d *  x).equals(cfdm.Data(a0 *  x.datum(), 'm2'), traceback=1))
#                    self.assertTrue((d /  x).equals(cfdm.Data(a0 /  x.datum(), '1' ), traceback=1))
#                    self.assertTrue((d -  x).equals(cfdm.Data(a0 -  x.datum(), 'm' ), traceback=1))
#                    self.assertTrue((d // x).equals(cfdm.Data(a0 // x.datum(), '1' ), traceback=1))
#    
#                    try:
#                       d ** x
#                    except:
#                        pass
#                    else:
#                        self.assertTrue((x**d).all(), '%s**%s' % (x, repr(d)))
#    
#                    self.assertTrue(d.__truediv__(x).equals(cfdm.Data(a0.__truediv__(x.datum()), ''), traceback=1))
#                #--- End: for
#            #--- End: for
#        #--- End: for
#
#        cfdm.CHUNKSIZE(self.original_chunksize)
#    #--- End: def

#    def test_Data_BROADCASTING(self):        
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        A = [numpy.array(3),
#             numpy.array( [3]),
#             numpy.array( [3]).reshape(1, 1),
#             numpy.array( [3]).reshape(1, 1, 1),
#             numpy.arange(  5).reshape(5, 1),
#             numpy.arange(  5).reshape(1, 5),
#             numpy.arange(  5).reshape(1, 5, 1),
#             numpy.arange(  5).reshape(5, 1, 1),
#             numpy.arange(  5).reshape(1, 1, 5),
#             numpy.arange( 25).reshape(1, 5, 5),
#             numpy.arange( 25).reshape(5, 1, 5),
#             numpy.arange( 25).reshape(5, 5, 1),
#             numpy.arange(125).reshape(5, 5, 5),
#        ]
#            
#        for chunksize in self.chunk_sizes:   
#            cfdm.CHUNKSIZE(chunksize) 
#            for a in A:
#                for b in A:
#                    d = cfdm.Data(a)
#                    e = cfdm.Data(b)
#                    ab = a*b
#                    de = d*e
#                    self.assertTrue(de.shape == ab.shape)
#                    self.assertTrue((de.array == ab).all())
#                #--- End: for
#            #--- End: for
#        #--- End: for
#
#        cfdm.CHUNKSIZE(self.original_chunksize)
#    #--- End: def

#    def test_Data_dumpd_loadd(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        for chunksize in self.chunk_sizes:   
#            cfdm.CHUNKSIZE(chunksize) 
#            
#            d = cfdm.read(self.filename)[0].data
#            
#            dumpd = d.dumpd()
#            self.assertTrue(d.equals(cfdm.Data(loadd=d.dumpd()), traceback=True))
#            self.assertTrue(d.equals(cfdm.Data(loadd=d.dumpd()), traceback=True))
#            d.to_disk()                        
#            self.assertTrue(d.equals(cfdm.Data(loadd=d.dumpd()), traceback=True))
#        #--- End: for
#        cfdm.CHUNKSIZE(self.original_chunksize)
#    #--- End: def

#--- End: class


if __name__ == "__main__":
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print''
    unittest.main(verbosity=2)
