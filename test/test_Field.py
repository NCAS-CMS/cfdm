import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class FieldTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        self.contiguous = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       'DSG_timeSeries_contiguous.nc')
        
        self.f = cfdm.read(self.filename)[0]

        self.test_only = []
#        self.test_only = ['test_Field_transpose','test_Field_squeeze']
        self.test_only = ['test_Field_match','test_Field_items']
#        self.test_only = ['test_Field_items']
#        self.test_only = ['test_Field_axes','test_Field_data_axes']
#        self.test_only = ['test_Field___getitem__']
#        self.test_only = ['test_Field___setitem__']
#        self.test_only = ['test_Field_expand_dims']
#        self.test_only = ['test_Field_field']

    def test_Field___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0].squeeze()
        d = f.array
        f = cfdm.read(self.filename)[0].squeeze()

        g = f[...]
        self.assertTrue((g.array == d).all())
        
        g = f[:, :]
        self.assertTrue((g.array == d).all())
        
        g = f[slice(None), :]
        self.assertTrue((g.array== d).all())
        
        g = f[:, slice(0, f.shape[1], 1)]
        self.assertTrue((g.array == d).all())
        
        g = f[slice(0, None, 1), slice(0, None)]
        self.assertTrue((g.array == d).all())
        
        g = f[3:7, 2:5]
        self.assertTrue((g.array == d[3:7, 2:5]).all())
        
        g = f[6:2:-1, 4:1:-1]
        self.assertTrue((g.array == d[6:2:-1, 4:1:-1]).all())

        g = f[[0, 3, 8], [1, 7, 8]]
        self.assertTrue(g.shape == (3, 3))
                
#        g = f[[8, 3, 0], [8, 7, 1]]
        
        g = f[[1, 4, 7], slice(6, 8)]
        self.assertTrue((g.array == d[[1, 4, 7], slice(6, 8)]).all())
    #--- End: def

    def test_Field___setitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0].squeeze()
        
        f[...] = 0
        self.assertTrue((f.array == 0).all())
        
        f[3:7, 2:5] = -1
        self.assertTrue((f.array[3:7, 2:5] == -1).all())

        f[6:2:-1, 4:1:-1] = numpy.array(-1)
        self.assertTrue((f.array[6:2:-1, 4:1:-1] == -1).all())

        index = ([0, 3, 8], [1, 7, 8])
        f[index] = -2
        self.assertTrue((f[index].array == -2).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        index = ([0, 3, 8], [1, 7, 8])

        f[index] = numpy.array([[[[-3]]]])
        self.assertTrue((f[index].array == -3).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = -4
        self.assertTrue((f[index].array == -4).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data(-5, None)
        self.assertTrue((f[index].array == -5).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data([-6.], f.Units)
        self.assertTrue((f[index].array == -6).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data([[-7]], None)
        self.assertTrue((f[index].array == -7).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = numpy.full((3, 3), -8.0)
        self.assertTrue((f[index].array == -8).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        index = ([7, 4, 1], slice(6, 8))
        f[index] = [-9]
        self.assertTrue((f[index].array == -9).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))
    #--- End: def

    def test_Field_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return


        f = self.f

        da = {'dim0': 1, 'dim1': 10, 'dim2': 9}

        self.assertTrue(f.axes() == da)

        self.assertTrue(f.axes() == {'dim0': cfdm.DomainAxis(1), 'dim1': cfdm.DomainAxis(10), 'dim2': cfdm.DomainAxis(9)})

        for key in f.data_axes():
            self.assertTrue(f.axis(key).size == da[key])

        for i in range(f.ndim):
            self.assertTrue(f.axis(i, key=True) == f.data_axes()[i])

        self.assertTrue(set(f.axes(slice(0,3))) == set(f.data_axes()))

        for k, v in f.ncdimensions.iteritems():
            self.assertTrue(f.axis('ncdim%'+v, key=True) == k)
    #--- End: def

    def test_Field_data_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertTrue(self.f.copy().data_axes() == ['dim0', 'dim1', 'dim2'])
        f = cfdm.Field(data=cfdm.Data(9))
        self.assertTrue(f.data_axes() == [])
        f.remove_data()
        self.assertTrue(f.data_axes() == None)
    #--- End: def

    def test_Field_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
        h = g.copy()
        h.data[...] = h.array + 1
        self.assertFalse(f.equals(h, traceback=False))
    #--- End: def

    def test_Field_expand_dims(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        
        g = f.copy()   
        g.expand_dims(copy=False)
        self.assertTrue(g.ndim == f.ndim + 1)
        self.assertTrue(g.data_axes()[1:] == f.data_axes())

        g = f.expand_dims(0)
        self.assertTrue(g.ndim == f.ndim + 1)
        self.assertTrue(g.data_axes()[1:] == f.data_axes())

        g = f.expand_dims(3)
        self.assertTrue(g.ndim == f.ndim + 1)
        self.assertTrue(g.data_axes()[:-1] == f.data_axes())

        g = f.expand_dims(-3)
        self.assertTrue(g.ndim == f.ndim + 1)
        self.assertTrue(g.data_axes()[1:] == f.data_axes())
    #--- End: def

    def test_Field_items(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]

        self.assertTrue(len(f.Items()) == 15)
        self.assertTrue(len(f.Items(role='damr')) == 9)

        self.assertTrue(len(f.items()) == 13)
        self.assertTrue(len(f.items(inverse=True)) == 0)

        self.assertTrue(len(f.items(ndim=1)) == 8)
        self.assertTrue(len(f.items(ndim=1, inverse=True)) == 5)

        self.assertTrue(len(f.items(ndim=2)) == 5)
        self.assertTrue(len(f.items(ndim=2, inverse=True)) == 8)

        self.assertTrue(len(f.items(ndim=4)) == 0)
        self.assertTrue(len(f.items(ndim=4, inverse=True)) == 13)

        self.assertTrue(len(f.items(role='d')) == 3)
        self.assertTrue(len(f.items(role='da')) == 6)
        self.assertTrue(len(f.items(role='dam')) == 7)

        self.assertTrue(len(f.items(axes='Y')) == 8)
        self.assertTrue(len(f.items(axes='Y', inverse=True)) == 5)

        self.assertTrue(len(f.items(axes='Z')) == 3)
        self.assertTrue(len(f.items(axes='Z', inverse=True)) == 10)
        
        self.assertTrue(len(f.items('X')) == 1)
        self.assertTrue(len(f.items('Y')) == 1)
        self.assertTrue(len(f.items('Z')) == 1)
        self.assertTrue(len(f.items('X', inverse=True)) == 12)
        self.assertTrue(len(f.items('Y', inverse=True)) == 12)
        self.assertTrue(len(f.items('Z', inverse=True)) == 12)
        self.assertTrue(len(f.items(['X', 'Y', {'standard_name': 'longitude', 'units': 'degrees_east'}])) == 3)
        self.assertTrue(len(f.items(['X', 'Y', {'standard_name': 'longitude', 'units': 'K'}])) == 2)

        self.assertTrue(len(f.items(ndim=2)) == 5)
        self.assertTrue(len(f.items(axes='X', ndim=2)) == 5)

        self.assertTrue(len(f.items('longitude', axes='X', ndim=2)) == 1)
        self.assertTrue(len(f.items('grid_longitude', axes='X', ndim=2)) == 0)

        self.assertTrue(len(f.items('atmosphere_hybrid_height_coordinate')) == 1)

        self.assertTrue(len(f.items(axes='X')) == 7)
        self.assertTrue(len(f.items(axes='Y')) == 8)
        self.assertTrue(len(f.items(axes='Z')) == 3)

        self.assertTrue(len(f.items(axes=['X','Y'])) == 10)
        self.assertTrue(len(f.items(axes=['X','Z'])) == 10)
        self.assertTrue(len(f.items(axes=['Z','Y'])) == 11)

        self.assertTrue(len(f.items(axes_all='X')) == 2)
        self.assertTrue(len(f.items(axes_all='Y')) == 3)
        self.assertTrue(len(f.items(axes_all='Z')) == 3)
        self.assertTrue(len(f.items(axes_all=['X','Y'])) == 5)
        self.assertTrue(len(f.items(axes_all=['X','Z'])) == 0)
        self.assertTrue(len(f.items(axes_all=['Z','Y'])) == 0)

        self.assertTrue(len(f.items(axes_subset='X')) == 7)
        self.assertTrue(len(f.items(axes_subset='Y')) == 8)
        self.assertTrue(len(f.items(axes_subset='Z')) == 3)
        self.assertTrue(len(f.items(axes_subset=['X','Y'])) == 5)
        self.assertTrue(len(f.items(axes_subset=['X','Z'])) == 0)
        self.assertTrue(len(f.items(axes_subset=['Z','Y'])) == 0)

        self.assertTrue(len(f.items(axes_superset='X')) == 2)
        self.assertTrue(len(f.items(axes_superset='Y')) == 3)
        self.assertTrue(len(f.items(axes_superset='Z')) == 3)

        self.assertTrue(len(f.items(axes_superset=['X','Y'])) == 10)
        self.assertTrue(len(f.items(axes_superset=['X','Z'])) == 5)
        self.assertTrue(len(f.items(axes_superset=['Z','Y'])) == 6)
    #--- End: def

    def test_Field_match(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        f.long_name = 'qwerty'
        f.ncvar = 'tas'
        all_kwargs = (
            {'description': None},
            {'description': {}},
            {'description': []},
            {'description': [None]},
            {'description': [{}]},
            {'description': [None, {}]},
            {'description': 'eastward_wind'},
            {'description': 'ncvar%tas'},
            {'description': 'long_name:qwerty'},
            {'description': 'standard_name:eastward_wind'},
            {'description': {'standard_name': 'eastward_wind'}},
            {'description': {'long_name': 'qwerty'}},
            {'description': {None: 'ncvar%tas'}},
            {'description': {None: 'eastward_wind'}},
            {'description': ['eastward_wind', 'foobar']},
            {'description': ['eastward_wind', 'ncvar%tas']},
            {'description': ['eastward_wind', 'ncvar%foo']},
            {'description': ['eastward_wind', {'long_name': 'qwerty'}]},
            {'description': ['eastward_wind', {'long_name': 'foobar'}]},
        )

        for kwargs in all_kwargs:
            self.assertTrue(f.match(**kwargs), 
                            'f.match(**{}) failed'.format(kwargs))
            kwargs['inverse'] = True
            self.assertFalse(f.match(**kwargs),
                             'f.match(**{}) failed'.format(kwargs))
        #--- End: for
    #--- End: def

    def test_Field_squeeze(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]

        f.squeeze(copy=False)
        g = f.copy()
        h = f.copy()
        i = h.squeeze(copy=False)
        self.assertTrue(f.equals(g))
        self.assertTrue(h is i)
    #--- End: def

    def test_Field_transpose(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]

        # Null transpose
        self.assertTrue(f is f.transpose([0, 1, 2], copy=False))
        self.assertTrue(f.equals(f.transpose([0, 1, 2])))

        f = cfdm.read(self.filename)[0]
        h = f.transpose((1, 2, 0))
        h0 = h.transpose(('atmos', 'grid_latitude', 'grid_longitude'))
        h.transpose((2, 0, 1), copy=False)
        h.transpose(('grid_longitude', 'atmos', 'grid_latitude'), copy=False)
        h.transpose(('atmos', 'grid_latitude', 'grid_longitude'), copy=False)
        self.assertTrue(cfdm.equals(h, h0, traceback=True))
        self.assertTrue((h.array==f.array).all())
    #--- End: def

#    def test_Field_field(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = cfdm.read(self.filename)[0]
#
#        y = f.field('grid_lat')
#        print y
#    #--- End: def

    def test_Field_item_items_role_r(self):
        f = cfdm.read(self.filename)[0]
        
        self.assertTrue(f.item('BLAH',  role='r') is None)
        self.assertTrue(f.item('atmos', role='r', key=True) == 'ref0')
        self.assertTrue(f.item('atmos', role='r', key=True, inverse=True) == 'ref1')

        self.assertTrue(set(f.items(role='r')) == set(['ref0', 'ref1']))
        self.assertTrue(set(f.items('BLAH', role='r')) == set())
        self.assertTrue(set(f.items('rot', role='r')) == set(['ref1']))
        self.assertTrue(set(f.items('rot', role='r', inverse=True)) == set(['ref0']))
        self.assertTrue(set(f.items('atmosphere_hybrid_height_coordinate', role='r', exact=True)) == set(['ref0']))
    #--- End: def
#--- End: class

if __name__ == '__main__':
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print''
    unittest.main(verbosity=2)
