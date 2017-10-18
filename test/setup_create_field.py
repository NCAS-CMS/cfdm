import datetime
import os
import sys
import unittest

import numpy

import cfdm

class create_fieldTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    def test_create_field(self):

        # Dimension coordinates
        dim1 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(10.), 'degrees'))
        dim1.standard_name = 'grid_latitude'

        dim0 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(9.) + 20, 'degrees'))
        dim0.standard_name = 'grid_longitude'
        dim0.data[-1] = 34
        bounds = cfdm.Data(numpy.array([dim0.data.array-0.5, dim0.data.array+0.5]).transpose((1,0)))
        bounds[-2,1] = 30
        bounds[-1,:] = [30, 36]
        dim0.insert_bounds(cfdm.Bounds(data=bounds))
        
        dim2 = cfdm.DimensionCoordinate(data=cfdm.Data(1.5), bounds=cfdm.Bounds(data=cfdm.Data([1, 2.])))
        dim2.standard_name = 'atmosphere_hybrid_height_coordinate'
        
        # Auxiliary coordinates
        ak = cfdm.DomainAncillary(data=cfdm.Data(10., 'm'))
        ak.id = 'atmosphere_hybrid_height_coordinate_ak'
        ak.insert_bounds(cfdm.Bounds(data=cfdm.Data([5, 15.])), ak.Units)
        
        bk = cfdm.DomainAncillary(data=cfdm.Data(20.))
        bk.id = 'atmosphere_hybrid_height_coordinate_bk'
        bk.insert_bounds(cfdm.Bounds(data=cfdm.Data([14, 26.])))
        
        aux2 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(-45, 45, dtype='int32').reshape(10, 9),
                         units='degree_N'))
        aux2.standard_name = 'latitude'
        
        aux3 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(60, 150, dtype='int32').reshape(9, 10),
                         units='degreesE'))
        aux3.standard_name = 'longitude'
        
        aux4 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(['alpha','beta','gamma','delta','epsilon',
                          'zeta','eta','theta','iota','kappa']))
        aux4.standard_name = 'greek_letters'
        aux4[0] = cfdm.masked
    
        # Cell measures
        msr0 = cfdm.CellMeasure(
            data=cfdm.Data(1+numpy.arange(90.).reshape(9, 10)*1234, 'km2'))
        msr0.measure = 'area'
        
        # Coordinate references
        ref0 = cfdm.CoordinateReference(
            name='rotated_latitude_longitude',
            parameters={'grid_north_pole_latitude': 38.0,
                        'grid_north_pole_longitude': 190.0})
        
        # Data          
        data = cfdm.Data(numpy.arange(90.).reshape(10, 9), 'm s-1')

        properties = {'standard_name': 'eastward_wind'}
        
        f = cfdm.Field(properties=properties, data=data)

        x = f.insert_dim(dim0)
        y = f.insert_dim(dim1)
        z = f.insert_dim(dim2)

        f.insert_aux(aux2)
        f.insert_aux(aux3)
        f.insert_aux(aux4, axes=['Y'])

        ak = f.insert_domain_anc(ak)
        bk = f.insert_domain_anc(bk)

        f.insert_measure(msr0)

        f.insert_ref(ref0)

        orog = cfdm.DomainAncillary(data=f.data)
        orog.standard_name = 'surface_altitude'
        orog = f.insert_domain_anc(orog, axes=['Y', 'X'])

        ref1 = cfdm.CoordinateReference(name='atmosphere_hybrid_height_coordinate',
                                        ancillaries={'orog': orog, 'a': ak, 'b': bk})

        f.insert_ref(ref1)

        # Field ancillary variables
#        g = f.transpose([1, 0])
        g = f.copy()
#        g.standard_name = 'ancillary0'
#        g *= 0.01
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryA'
        f.insert_field_anc(anc, axes=['Y', 'X'])

        g = f[0]
        g.squeeze(copy=False)
#        g.standard_name = 'ancillary2'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryB'
        f.insert_field_anc(anc, axes=['X'])

        g = f[..., 0]
        g = g.squeeze()
#        g.standard_name = 'ancillary3'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryC'
        f.insert_field_anc(anc, axes=['Y'])

        f.flag_values = [1,2,4]
        f.flag_meanings = ['a', 'bb', 'ccc']      

        f.insert_cell_methods('grid_longitude: mean grid_latitude: max')

        # Write the file, and read it in
#        print f.shape
        cfdm.write(f, self.filename, _debug=True)

        g = cfdm.read(self.filename, _debug=False, squeeze=True)
        
#        print '\n GGGG =============================================='
#        print f
#        print g
#        r =    g[0].item('atmos', role='r')
#        print  r.items()
#        print g.dump()
#        print 'GGGG =============================================='


        self.assertTrue(len(g) == 1)
        
#        print f
##        print g
#        print f.items()
#        f.dump()
##        g.dump()

        g = g[0]
        g.squeeze(copy=False)

        self.assertTrue(sorted(f.items().keys()) ==  sorted(g.items().keys()))

#        for key in sorted(f.items().keys()):
#            print key, repr(f.item(key))
#            print '    ', repr(g.item(key))
        
        self.assertTrue(g.equals(f, traceback=True), "Field not equal to itself read back in")
        
        x = g.dump(display=False)
        x = f.dump(display=False)
    #--- End: def

#--- End: class

if __name__ == "__main__":
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print ''
    unittest.main(verbosity=2)
