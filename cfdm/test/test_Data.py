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

def axes_combinations(ndim):
    return  [axes
             for n in range(1, ndim+1)
             for axes in itertools.permutations(range(ndim), n)]


class DataTest(unittest.TestCase):
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

        self.test_only = []
        #    self.test_only = ['NOTHING!!!!!']
        #    self.test_only = ['test_Data__asdatetime__asreftime__isdatetime']
        #    self.test_only = ['test_Data__setitem__']
        #    self.test_only = ['test_Data_ceil', 'test_Data_floor',
        #                      'test_Data_trunc', 'test_Data_rint']
        #    self.test_only = ['test_Data_array', 'test_Data_datetime_array']
        #    self.test_only = ['test_dumpd_loadd']
        #    self.test_only = ['test_Data_BINARY_AND_UNARY_OPERATORS']

    def test_Data_any(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.Data([[0, 0, 0]])
        self.assertFalse(d.any())
        d[0, 0] = numpy.ma.masked
        self.assertFalse(d.any())
        d[0, 1] = 3
        self.assertTrue(d.any())
        d[...] = numpy.ma.masked
        self.assertFalse(d.any())

    def test_Data__repr__str(self):
        '''Check cf.Data.__repr__, cf.Data.__str__'''
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

#    def test_Data__getitem__(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return

    def test_Data__setitem__(self):
        '''Check cf.Data.__setitem__'''
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
            for dvalue, avalue in ((n, n),
                                   (cfdm.masked, numpy.ma.masked),
                                   (n, n)):
                message = "cfdm.Data[{}, {}]={}={} failed".format(
                    j, i, dvalue, avalue)
                d[j, i] = dvalue
                a[j, i] = avalue
                x = d.array
                self.assertTrue((x == a).all() in (True, numpy.ma.masked),
                                message)
                m = numpy.ma.getmaskarray(x)
                self.assertTrue((m == numpy.ma.getmaskarray(a)).all(),
                                'd.mask.array='+repr(m)+'\nnumpy.ma.getmaskarray(a)='+repr(numpy.ma.getmaskarray(a)))
        # --- End: for

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
        # --- End: for

        # Scalar numeric array
        d = cfdm.Data(9, units='km')
        d[...] = cfdm.masked
        a = d.array
        self.assertTrue(a.shape == ())
        self.assertIs(a[()], numpy.ma.masked)

    def test_Data_apply_masking(self):
        '''Check cf.Data.apply_masking'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.arange(12).reshape(3, 4)
        a[1, 1] = numpy.ma.masked

        d = cfdm.Data(a, units='m')

        self.assertTrue((a == d.array).all())
        self.assertTrue((a.mask == d.mask.array).all())

        b = a.copy()
        e = d.apply_masking()
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a==0, numpy.ma.masked, a)
        e = d.apply_masking(fill_values=[0])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a==0) | (a==11), numpy.ma.masked, a)
        e = d.apply_masking(fill_values=[0, 11])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a<3, numpy.ma.masked, a)
        e = d.apply_masking(valid_min=3)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where(a>6, numpy.ma.masked, a)
        e = d.apply_masking(valid_max=6)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a<2) | (a>8), numpy.ma.masked, a)
        e = d.apply_masking(valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        d.set_fill_value(7)

        b = numpy.ma.where(a==7, numpy.ma.masked, a)
        e = d.apply_masking(fill_values=True)
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

        b = numpy.ma.where((a==7) | (a<2) | (a>8), numpy.ma.masked, a)
        e = d.apply_masking(fill_values=True, valid_range=[2, 8])
        self.assertTrue((b == e.array).all())
        self.assertTrue((b.mask == e.mask.array).all())

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

    def test_Data_array(self):
        '''Check cf.Data.array'''
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
        self.assertIs(a[()], numpy.ma.masked)

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

    def test_Data_datetime_array(self):
        '''Check cf.Data.datetime_array'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        d = cfdm.Data([11292.5, 11293], units='days since 1970-1-1')
        dt = d.datetime_array
        self.assertTrue(dt[0] == datetime.datetime(2000, 12, 1, 12, 0))
        self.assertTrue(dt[1] == datetime.datetime(2000, 12, 2,  0, 0))

        d[0] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[0], numpy.ma.masked)
        self.assertTrue(dt[1] == datetime.datetime(2000, 12, 2,  0, 0))

        d = cfdm.Data(11292.5, units='days since 1970-1-1')
        dt = d.datetime_array
        self.assertTrue(dt[()] == datetime.datetime(2000, 12, 1, 12, 0))

        d[()] = cfdm.masked
        dt = d.datetime_array
        self.assertIs(dt[()], numpy.ma.masked)

    def test_Data_flatten(self):
        '''Check cf.Data.flatten'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        ma = numpy.ma.arange(24).reshape(1, 2, 3, 4)
        ma[0, 1, 1, 2] = cfdm.masked
        ma[0, 0, 2, 1] = cfdm.masked

        d = cfdm.Data(ma.copy())
        self.assertTrue(d.equals(d.flatten([]), verbose=3))
        self.assertIsNone(d.flatten(inplace=True))

        d = cfdm.Data(ma.copy())

        b = ma.flatten()
        for axes in (None, list(range(d.ndim))):
            e = d.flatten(axes)
            self.assertTrue(e.ndim == 1)
            self.assertTrue(e.shape == b.shape)
            self.assertTrue(e.equals(cfdm.Data(b), verbose=3))

        for axes in axes_combinations(d.ndim):
            e = d.flatten(axes)

            if len(axes) <= 1:
                shape  = d.shape
            else:
                shape = [n for i, n in enumerate(d.shape) if i not in axes]
                shape.insert(
                    sorted(axes)[0],
                    numpy.prod([n
                                for i, n in enumerate(d.shape) if i in axes]))

            self.assertTrue(e.shape == tuple(shape))
            self.assertTrue(e.ndim == d.ndim-len(axes)+1)
            self.assertTrue(e.size == d.size)

    def test_Data_transpose(self):
        '''Check cf.Data.transpose'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.arange(10*15*19).reshape(10, 1, 15, 19)
        d = cfdm.Data(a.copy())

        for indices in (list(range(a.ndim)), list(range(-a.ndim, 0))):
            for axes in itertools.permutations(indices):
                a = numpy.transpose(a, axes)
                d = d.transpose(axes)
                message = "cfdm.Data.transpose({}) failed: d.shape={}, a.shape={}".format(
                    axes, d.shape, a.shape)
                self.assertTrue(d.shape == a.shape, message)
                self.assertTrue((d.array == a).all(), message)
        # --- End: for

    def test_Data_unique(self):
        '''Check cf.Data.unique'''
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

    def test_Data_equals(self):
        '''Check cf.Data.equals'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.arange(10*15*19).reshape(10, 1, 15, 19)
        a[0, 0, 2, 3] = numpy.ma.masked

        d = cfdm.Data(a, units='days since 2000-2-2', calendar='noleap')
        e = copy.deepcopy(d)

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))

    def test_Data_max_min_sum_squeeze(self):
        '''Check cf.Data.maximum, cf.Data.minumum, cf.Data.sum,
    cf.Data.squeeze'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.arange(10*15*19).reshape(10, 1, 15, 19)
        a[0, 0, 0, 0] = numpy.ma.masked
        a[-1, -1, -1, -1] = numpy.ma.masked
        a[5, -1, 6, 10] = numpy.ma.masked
        d = cfdm.Data(a)

        b = a.max()
        x = d.maximum().squeeze()
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=0)
        x = d.maximum(axes=0).squeeze(0)
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.max(axis=(0, 3))
        x = d.maximum(axes=[0, 3]).squeeze([0, 3])
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min()
        x = d.minimum().squeeze()
        self.assertTrue(x.shape == b.shape)
        self.assertTrue((x.array == b).all())

        b = a.min(axis=(0, 3))
        x = d.minimum(axes=[0, 3]).squeeze([0, 3])
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

    def test_Data_dtype_mask(self):
        '''Check cf.Data.dtype, cf.Data.mask'''
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        a = numpy.ma.array([[280.0,   -99,   -99,   -99],
                            [281.0, 279.0, 278.0, 279.0]],
                           dtype=float,
                           mask=[[0, 1, 1, 1],
                                 [0, 0, 0, 0]])

        d = cfdm.Data([[280, -99, -99, -99],
                       [281, 279, 278, 279]])
        self.assertTrue(d.dtype == numpy.dtype(int))

        d = cfdm.Data([[280, -99, -99, -99],
                       [281, 279, 278, 279]],
                      dtype=float,
                      mask=[[0, 1, 1, 1],
                            [0, 0, 0, 0]])

        self.assertTrue(d.dtype==a.dtype)
        self.assertTrue((d.array==a).all())
        self.assertTrue(d.mask.shape==a.mask.shape)
        self.assertTrue((d.mask.array==numpy.ma.getmaskarray(a)).all())

        a = numpy.array([[280.0,   -99,   -99,   -99],
                         [281.0, 279.0, 278.0, 279.0]],
                        dtype=float)
        mask = numpy.ma.masked_all(a.shape).mask

        d = cfdm.Data([[280, -99, -99, -99],
                       [281, 279, 278, 279]],
                      dtype=float)

        self.assertTrue(d.dtype==a.dtype)
        self.assertTrue((d.array==a).all())
        self.assertTrue(d.mask.shape==mask.shape)
        self.assertTrue((d.mask.array==numpy.ma.getmaskarray(a)).all())


# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
