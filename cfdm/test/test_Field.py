from __future__ import print_function
import collections
import datetime
import inspect
import os
import re
import unittest

import numpy

import cfdm

class FieldTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        self.contiguous = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       'DSG_timeSeries_contiguous.nc')
        self.indexed = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'DSG_timeSeries_indexed.nc')
        self.indexed_contiguous = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               'DSG_timeSeriesProfile_indexed_contiguous.nc')

        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={}'.format(f))
        self.f = f[0]

        self.test_only = []
#        self.test_only = ['test_Field_constructs']
#        self.test_only = ['test_Field_domain_axes']
#        self.test_only = ['test_Field_axes','test_Field_data_axes']
#        self.test_only = ['test_Field___getitem__']
#        self.test_only = ['test_Field___setitem__']
#        self.test_only = ['test_Field_field']


    def test_Field__repr__str__dump_construct_type(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f
        
        _ = repr(f)
        _ = str(f)
        _ = f.dump(display=False)
        self.assertTrue(f.construct_type == 'field')


    def test_Field___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        f = f.squeeze()
        
        d = f.data.array
        
        g = f[...]
        self.assertTrue((g.data.array == d).all())
        
        g = f[:, :]
        self.assertTrue((g.data.array == d).all())
        
        g = f[slice(None), :]
        self.assertTrue((g.data.array == d).all())
        
        g = f[slice(None), slice(None)]
        self.assertTrue((g.data.array == d).all())
        
        g = f[slice(None), ...]
        self.assertTrue((g.data.array == d).all())
        
        g = f[..., slice(None)]
        self.assertTrue((g.data.array == d).all())
        
        g = f[:, slice(0, f.data.shape[1], 1)]
        self.assertTrue((g.data.array == d).all())
        
        for indices, shape, multiple_list_indices in (
                [(slice(0, None, 1), slice(0, None)) , (10, 9), False],
                [(slice(3, 7)      , slice(2, 5))    , ( 4, 3), False],
                [(slice(6, 2, -1)  , slice(4, 1, -1)), ( 4, 3), False],
#               [(1                , 3)              , ( 1, 1), False],
#               [(-2               , -4)             , ( 1, 1), False],
#               [(-2               , slice(1, 5))    , ( 1, 4), False],
#               [(slice(5, 1, -2)  , 7)              , ( 2, 1), False],
                [([1, 4, 7]        , slice(1, 5))    , ( 3, 4), False],
                [([1, 4, 7]        , slice(6, 8))    , ( 3, 2), False],
                [(slice(6, 8)      , [1, 4, 7])      , ( 2, 3), False],
                [([0, 3, 8]        , [1, 7, 8])      , ( 3, 3), True],
                [([8, 3, 0]        , [8, 7, 1])      , ( 3, 3), True]
        ):
            g = f[indices]

            if not multiple_list_indices:
                e = d[indices]
            else:
                e = d.copy()
                indices = list(indices)
                for axis, i in enumerate(indices):
                    if isinstance(i, list):
                        e = numpy.take(e, indices=i, axis=axis)
                        indices[axis] = slice(None)
    
                e = e[tuple(indices)]
            #--- End: if
            
            self.assertTrue(g.data.shape == e.data.shape,
                            'Bad shape for {}: {} != {}'.format(
                                indices,
                                g.data.shape,
                                e.data.shape))
            self.assertTrue((g.data.array == e).all(),
                            'Bad values for {}: {} != {}'.format(indices,
                                                                 g.data.array,
                                                                 e))
        #--- End: for

        # Check slicing of bounds
        g = f[..., 0:4]
        c = g.construct('grid_longitude')
        b = c.bounds
        self.assertTrue(c.data.shape == (4,))
        self.assertTrue(b.data.shape == (4, 2))


#    def test_Field___setitem__(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = self.f.squeeze()
#        
#        f[...] = 0
#        self.assertTrue((f.data.array == 0).all())
#
#        f[:, :] = 0
#        self.assertTrue((f.data.array == 0).all())
#
#
#        for indices in [
#                (slice(None)    , slice(None)),
#                (slice(3, 7)    , slice(None)),
#                (slice(None)    , slice(2, 5)),
#                (slice(3, 7)    , slice(2, 5)),
#                (slice(6, 2, -1), slice(4, 1, -1)),
#                (slice(2, 6)    , slice(4, 1, -1)),
#                ([0, 3, 8]      , [1, 7, 8]),
#                ([7, 4, 1]      , slice(6, 8)),
#        ]:
#            f[...] = 0
#            f[indices] = -1
#            array = f[indices].data.array
#            self.assertTrue((array == -1).all())
#            
#            values, counts = numpy.unique(f.data.array, return_counts=True)
#            self.assertTrue(counts[0] == array.size)


    def test_Field_PROPERTIES(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        for name, value in f.properties().items():
            self.assertTrue(f.has_property(name))
            _ = f.get_property(name)
            _ = f.del_property(name)
            self.assertTrue(f.del_property(name, default=None) == None)
            self.assertTrue(f.get_property(name, default=None) == None)
            self.assertFalse(f.has_property(name))
            f.set_property(name, value)

        _ = f.clear_properties()
        f.set_properties(_)
        f.set_properties(_, copy=False)


    def test_Field_DATA(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        self.assertTrue(f.has_data())
        data = f.get_data()
        _ = f.del_data()
        _ = f.get_data(default=None)
        _ = f.del_data(default=None)
        self.assertFalse(f.has_data())
        _ = f.set_data(data, axes=None)
        _ = f.set_data(data, axes=None, copy=False)
        self.assertTrue(f.has_data())                

        f = self.f.copy()
        _ = f.del_data_axes()
        self.assertFalse(f.has_data_axes())
        self.assertTrue(f.del_data_axes(default=None) == None)

        f = self.f.copy()
        for key in f.constructs.filter_by_data():
            self.assertTrue(f.has_data_axes(key))
            _ = f.get_data_axes(key)
            _ = f.del_data_axes(key)
            self.assertTrue(f.del_data_axes(key, default=None) == None)
            self.assertTrue(f.get_data_axes(key, default=None) == None)
            self.assertFalse(f.has_data_axes(key))


    def test_Field_CONSTRUCTS(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return
        
        f = self.f.copy()

        _ = f.construct('latitude')
        self.assertTrue(f.construct('NOT_latitude', default=None) == None)
        self.assertTrue(f.construct(re.compile('^l'), default=None) == None)

        key = f.construct_key('latitude')
        _ = f.get_construct(key)
        self.assertTrue(f.get_construct('qwerty', default=None) == None)

        constructs = self.f.auxiliary_coordinates
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} auxiliary coordinate constructs, expected {}'.format(len(constructs), n))               
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.AuxiliaryCoordinate)

        constructs = self.f.cell_measures
        n = 1
        self.assertTrue(len(constructs) == n,
                        'Got {} cell measure constructs, expected {}'.format(len(constructs), n))               
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMeasure)

        constructs = self.f.cell_methods
        n = 2
        self.assertTrue(len(constructs) == n,
                        'Got {} cell method constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CellMethod)
    
        ordered = self.f.cell_methods.ordered()        
        self.assertIsInstance(ordered, collections.OrderedDict)
    
        constructs = self.f.coordinate_references
        n = 2
        self.assertTrue(len(constructs) == n,
                        'Got {} ccoordinate reference onstructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.CoordinateReference)
  
        constructs = self.f.dimension_coordinates
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} dimension coordinate constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DimensionCoordinate)
            
        constructs = self.f.domain_ancillaries
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} domain ancillary constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAncillary)

        constructs = self.f.domain_axes
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} domain axis constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.DomainAxis)

        constructs = self.f.field_ancillaries
        n = 3
        self.assertTrue(len(constructs) == n,
                        'Got {} field ancillary constructs, expected {}'.format(len(constructs), n))
        for key, value in constructs.items():
            self.assertIsInstance(value, cfdm.FieldAncillary)

        # Domain axis key
        f = self.f
        ckey = f.construct_key('grid_latitude')
        dakey = f.get_data_axes(ckey)[0]
        self.assertTrue(f.domain_axis_key('grid_latitude') == dakey)        
        self.assertTrue(f.domain_axis_key('XXXX_latitude', default=None) == None)
        self.assertTrue(f.domain_axis_key(re.compile('^grid_'), default=None) == None)


    def test_Field_data_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        ref = f.get_data_axes()
        
        self.assertTrue(f.get_data_axes(default=None) == ref)

        self.assertTrue(f.del_data_axes() == ref)
        self.assertTrue(f.del_data_axes(default=None) == None)        
        
        self.assertTrue(f.set_data_axes(ref) == None)
        self.assertTrue(f.get_data_axes() == ref)


    def test_Field_convert(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        key = f.construct_key('grid_latitude')        
        c = f.convert(key)

        self.assertTrue(c.data.ndim == 1)
        self.assertTrue(c.get_property('standard_name') == 'grid_latitude')
        self.assertTrue(len(c.dimension_coordinates) == 1)
        self.assertTrue(len(c.auxiliary_coordinates) == 1)
        self.assertTrue(len(c.cell_measures) == 0)
        self.assertTrue(len(c.coordinate_references) == 1)
        self.assertTrue(len(c.domain_ancillaries) == 0)
        self.assertTrue(len(c.field_ancillaries) == 0)
        self.assertTrue(len(c.cell_methods) == 0)

        key = f.construct_key('latitude')        
        c = f.convert(key)
        
        self.assertTrue(c.data.ndim == 2)
        self.assertTrue(c.get_property('standard_name') == 'latitude')
        self.assertTrue(len(c.dimension_coordinates) == 2)
        self.assertTrue(len(c.auxiliary_coordinates) == 3)
        self.assertTrue(len(c.cell_measures) == 1)
        self.assertTrue(len(c.coordinate_references) == 1)
        self.assertTrue(len(c.domain_ancillaries) == 0)
        self.assertTrue(len(c.field_ancillaries) == 0)
        self.assertTrue(len(c.cell_methods) == 0)

        with self.assertRaises(ValueError):
            f.convert('qwerty')


    def test_Field_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        self.assertTrue(f.equals(f, verbose=True))
 
        g = f.copy()
        self.assertTrue(f.equals(g, verbose=True))
        self.assertTrue(g.equals(f, verbose=True))

        g = f[...]
        self.assertTrue(f.equals(g, verbose=True))
        self.assertTrue(g.equals(f, verbose=True))

        g = g.squeeze()
        self.assertFalse(f.equals(g))

        h = f.copy()
        h.data[...] = h.data.array[...] + 1
        self.assertFalse(f.equals(h))


    def test_Field_del_construct(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        a = f.del_construct('auxiliarycoordinate1')
        self.assertTrue(a.construct_type == 'auxiliary_coordinate')

        try:
            a = f.del_construct('auxiliarycoordinate1')
        except ValueError:
            pass
            
        a = f.del_construct('auxiliarycoordinate1', default=None)
        self.assertTrue(a == None)        


    def test_Field_has_construct(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        b = f.has_construct('auxiliarycoordinate1')
        self.assertTrue(b)

        f.del_construct('auxiliarycoordinate1')
        c = f.has_construct('auxiliarycoordinate1')
        self.assertTrue(not c)  # now expect False as we deleted the construct

        # Test edge case whereby constructs have Falsy values as key names:
        f.set_construct(cfdm.DomainAxis(0), key='')
        d = f.has_construct('')
        self.assertTrue(d)


    def test_Field_squeeze_transpose_insert_dimension(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        g = f.transpose()
        self.assertTrue(g.data.shape == f.data.shape[::-1])
        self.assertTrue(g.get_data_axes() == f.get_data_axes()[::-1])

        g = f.squeeze()
        self.assertTrue(g.data.shape == f.data.shape[1:])
        self.assertTrue(g.get_data_axes() == f.get_data_axes()[1:], (g.get_data_axes(), f.get_data_axes()))
        
        f = f.copy()
        g = f.copy()

        key = g.set_construct(cfdm.DomainAxis(1))
        h = g.insert_dimension(axis=key)
        self.assertTrue(h.data.ndim == f.data.ndim + 1)
        self.assertTrue(h.get_data_axes()[1:] == f.get_data_axes())

        key = g.set_construct(cfdm.DomainAxis(1))
        h = g.insert_dimension(position=g.data.ndim, axis=key)
        self.assertTrue(h.data.ndim == f.data.ndim + 1)
        self.assertTrue(h.get_data_axes()[:-1] == f.get_data_axes())


    def test_Field_compress_uncompress(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        methods = ('contiguous', 'indexed', 'indexed_contiguous')
        
        for method in methods:
            message = 'method='+method
            for f in cfdm.read(getattr(self, method)):
#                print(f)
                self.assertTrue(bool(f.data.get_compression_type()), message)

                u = f.uncompress()
                self.assertFalse(bool(u.data.get_compression_type()), message)
                self.assertTrue(f.equals(u, verbose=True), message)

                for method1 in methods:
                    message += ', method1='+method1
                    if method1 == 'indexed_contiguous':
                        if f.data.ndim != 3:
                            continue
                    elif f.data.ndim != 2:
                        continue
                    
#                    print(method, method1, f.data.ndim)

                    c = u.compress(method1)

                    self.assertTrue(bool(c.data.get_compression_type()), message)

                    self.assertTrue(u.equals(c, verbose=True), message)
                    self.assertTrue(f.equals(c, verbose=True), message)
                    
                    c = f.compress(method1)
                    self.assertTrue(bool(c.data.get_compression_type()), message)

                    self.assertTrue(u.equals(c, verbose=True), message)
                    self.assertTrue(f.equals(c, verbose=True), message)

                    cfdm.write(c, 'delme.nc')
                    c = cfdm.read('delme.nc')[0]

                    self.assertTrue(bool(c.data.get_compression_type()), message)
                    self.assertTrue(f.equals(c, verbose=True), message)
        #--- End: for
        
        
#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
