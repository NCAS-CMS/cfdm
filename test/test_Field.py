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
#        self.test_only = ['test_Field_domain_axes']
#        self.test_only = ['test_Field_axes','test_Field_data_axes']
#        self.test_only = ['test_Field___getitem__']
#        self.test_only = ['test_Field___setitem__']
#        self.test_only = ['test_Field_expand_dims']
#        self.test_only = ['test_Field_field']

    def test_Field___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0].squeeze()
        d = f.get_array()
        f = cfdm.read(self.filename)[0].squeeze()

        g = f[...]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[:, :]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[slice(None), :]
        self.assertTrue((g.get_array()== d).all())
        
        g = f[:, slice(0, f.shape[1], 1)]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[slice(0, None, 1), slice(0, None)]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[3:7, 2:5]
        self.assertTrue((g.get_array() == d[3:7, 2:5]).all())
        
        g = f[6:2:-1, 4:1:-1]
        self.assertTrue((g.get_array() == d[6:2:-1, 4:1:-1]).all())

        g = f[[0, 3, 8], [1, 7, 8]]
        self.assertTrue(g.shape == (3, 3))
                
#        g = f[[8, 3, 0], [8, 7, 1]]
        
        g = f[[1, 4, 7], slice(6, 8)]
        self.assertTrue((g.get_array() == d[[1, 4, 7], slice(6, 8)]).all())
    #--- End: def

    def test_Field___setitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0].squeeze()
        
        f[...] = 0
        self.assertTrue((f.get_array() == 0).all())
        
        f[3:7, 2:5] = -1
        self.assertTrue((f.get_array()[3:7, 2:5] == -1).all())

        f[6:2:-1, 4:1:-1] = numpy.array(-1)
        self.assertTrue((f.get_array()[6:2:-1, 4:1:-1] == -1).all())

        index = ([0, 3, 8], [1, 7, 8])
        f[index] = -2
        self.assertTrue((f[index].get_array() == -2).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        index = ([0, 3, 8], [1, 7, 8])

        f[index] = numpy.array([[[[-3]]]])
        self.assertTrue((f[index].get_array() == -3).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = -4
        self.assertTrue((f[index].get_array() == -4).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data(-5, None)
        self.assertTrue((f[index].get_array() == -5).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data([-6.], f.Units)
        self.assertTrue((f[index].get_array() == -6).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = cfdm.Data([[-7]], None)
        self.assertTrue((f[index].get_array() == -7).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        f[index] = numpy.full((3, 3), -8.0)
        self.assertTrue((f[index].get_array() == -8).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))

        index = ([7, 4, 1], slice(6, 8))
        f[index] = [-9]
        self.assertTrue((f[index].get_array() == -9).all(),
                        '\n'+repr(f.array)+'\n'+repr(f[index].array))
    #--- End: def

    def test_Field_auxiliary_coordinates(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        auxiliary_coordinates = f.auxiliary_coordinates()
                
        self.assertTrue(len(auxiliary_coordinates) == 3)

        for key, value in auxiliary_coordinates.iteritems():
            self.assertTrue(isinstance(value, cfdm.AuxiliaryCoordinate))
    #--- End: def

    def test_Field_cell_measures(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        constructs = f.cell_measures()
                
        self.assertTrue(len(constructs) == 1)

        for key, value in constructs.iteritems():
            self.assertTrue(isinstance(value, cfdm.CellMeasure))
    #--- End: def

    def test_Field_cell_methods(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        constructs = f.cell_methods()
                
        self.assertTrue(len(constructs) == 2)

        for key, value in constructs.iteritems():
            self.assertTrue(isinstance(value, cfdm.CellMethod))
    #--- End: def

    def test_Field_coordinate_references(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        constructs = f.coordinate_references()
                
        self.assertTrue(len(constructs) == 2)

        for key, value in constructs.iteritems():
            self.assertTrue(isinstance(value, cfdm.CoordinateReference))
    #--- End: def

    def test_Field_data_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        ref = ('domainaxis0', 'domainaxis1', 'domainaxis2')
        
        self.assertTrue(f.get_data_axes() == ref)
        self.assertTrue(f.get_data_axes(None) == ref)

        self.assertTrue(f.del_data_axes() == ref)
        self.assertTrue(f.del_data_axes() == None)        
        
        self.assertTrue(f.set_data_axes(ref) == None)
        self.assertTrue(f.get_data_axes() == ref)
    #--- End: def

    def test_Field_dimension_coordinates(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        dimension_coordinates = f.dimension_coordinates()
                
        self.assertTrue(len(dimension_coordinates) == 3)

        for key, value in dimension_coordinates.iteritems():
            self.assertTrue(isinstance(value, cfdm.DimensionCoordinate))
    #--- End: def

    def test_Field_domain_ancillaries(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        constructs = f.domain_ancillaries()
                
        self.assertTrue(len(constructs) == 3)

        for key, value in constructs.iteritems():
            self.assertTrue(isinstance(value, cfdm.DomainAncillary))
    #--- End: def

    def test_Field_domain_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        domain_axes = f.domain_axes()
        
        self.assertTrue(len(domain_axes) == 3)

        for key, value in domain_axes.iteritems():
            self.assertTrue(isinstance(value, cfdm.DomainAxis))
    #--- End: def

    def test_Field_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
        h = g.copy()
        h.data[...] = h.get_array() + 1
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

    def test_Field_field_ancillaries(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f

        constructs = f.field_ancillaries()
                
        self.assertTrue(len(constructs) == 3)

        for key, value in constructs.iteritems():
            self.assertTrue(isinstance(value, cfdm.FieldAncillary))
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

#    def test_Field_construct_axes(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = self.f.copy()
#
#    #--- End: def

    def test_Field_squeeze(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]

        f.squeeze(copy=False)
        g = f.copy()
        h = f.copy()
        i = h.squeeze(copy=False)
        self.assertTrue(f.equals(g, traceback=True))
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
        self.assertTrue((h.array==f.get_array()).all())
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

#--- End: class

if __name__ == '__main__':
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print''
    unittest.main(verbosity=2)
