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
        dim1 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(10.)))
        dim1.setprop('standard_name', 'grid_latitude')
        dim1.setprop('units', 'degrees')

        dim0 = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(9.) + 20))
        dim0.setprop('standard_name', 'grid_longitude')
        dim0.setprop('units', 'degrees')
        dim0.data[-1] = 34
        bounds = cfdm.Data(numpy.array([dim0.data.array-0.5, dim0.data.array+0.5]).transpose((1,0)))
        bounds[-2,1] = 30
        bounds[-1,:] = [30, 36]
        dim0.insert_bounds(cfdm.Bounds(data=bounds))
        
        dim2 = cfdm.DimensionCoordinate(data=cfdm.Data([1.5]), bounds=cfdm.Bounds(data=cfdm.Data([[1, 2.]])))
        dim2.setprop('standard_name', 'atmosphere_hybrid_height_coordinate')
        
        # Auxiliary coordinates
        ak = cfdm.DomainAncillary(data=cfdm.Data([10.])) #, 'm'))
        ak.setprop('units', 'm')
        ak.id = 'atmosphere_hybrid_height_coordinate_ak'
        ak.insert_bounds(cfdm.Bounds(data=cfdm.Data([[5, 15.]]))) # , ak.Units)
        
        bk = cfdm.DomainAncillary(data=cfdm.Data([20.]))
        bk.id = 'atmosphere_hybrid_height_coordinate_bk'
        bk.insert_bounds(cfdm.Bounds(data=cfdm.Data([[14, 26.]])))
        
        aux2 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(-45, 45, dtype='int32').reshape(10, 9)))
        aux2.setprop('units', 'degree_N')
        aux2.setprop('standard_name', 'latitude')
        
        aux3 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(numpy.arange(60, 150, dtype='int32').reshape(9, 10)))
        aux3.setprop('standard_name', 'longitude')
        aux3.setprop('units', 'degreeE')
                
        aux4 = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(['alpha','beta','gamma','delta','epsilon',
                          'zeta','eta','theta','iota','kappa']))
        aux4.setprop('standard_name', 'greek_letters')
        aux4[0] = cfdm.masked
    
        # Cell measures
        msr0 = cfdm.CellMeasure(
            data=cfdm.Data(1+numpy.arange(90.).reshape(9, 10)*1234))
        msr0.measure('area')
        msr0.setprop('units', 'km2')
        
        # Data          
        data = cfdm.Data(numpy.arange(90.).reshape(10, 9))

        properties = {'units': 'm s-1'}
        
        f = cfdm.Field(properties=properties)
        f.setprop('standard_name', 'eastward_wind')
        
        axisX = f.insert_domain_axis(cfdm.DomainAxis(9))
        axisY = f.insert_domain_axis(cfdm.DomainAxis(10))
        axisZ = f.insert_domain_axis(cfdm.DomainAxis(1))

        f.insert_data(data, axes=[axisY, axisX])
        
        x = f.insert_dimension_coordinate(dim0, axes=[axisX])
        y = f.insert_dimension_coordinate(dim1, axes=[axisY])
        z = f.insert_dimension_coordinate(dim2, axes=[axisZ])

        lat = f.insert_auxiliary_coordinate(aux2, axes=[axisY, axisX])
        lon = f.insert_auxiliary_coordinate(aux3, axes=[axisX, axisY])
        greek = f.insert_auxiliary_coordinate(aux4, axes=[axisY])

        ak = f.insert_domain_ancillary(ak, axes=[axisZ])
        bk = f.insert_domain_ancillary(bk, axes=[axisZ])

        # Coordinate references
        ref0 = cfdm.CoordinateReference(
            name='rotated_latitude_longitude',
            parameters={'grid_north_pole_latitude': 38.0,
                        'grid_north_pole_longitude': 190.0},
            coordinates=[x, y, lat, lon])

        f.insert_cell_measure(msr0, axes=[axisX, axisY])

        f.insert_coordinate_reference(ref0)

        orog = cfdm.DomainAncillary(data=f.data)
        orog.setprop('standard_name', 'surface_altitude')
        orog = f.insert_domain_ancillary(orog, axes=[axisY, axisX])

        ref1 = cfdm.CoordinateReference(name='atmosphere_hybrid_height_coordinate',
                                        domain_ancillaries={'orog': orog, 'a': ak, 'b': bk},
                                        coordinates=[z])

        ref1 = f.insert_coordinate_reference(ref1)

        # Field ancillary variables
#        g = f.transpose([1, 0])
        g = f.copy()
#        g.standard_name = 'ancillary0'
#        g *= 0.01
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryA'
        f.insert_field_ancillary(anc, axes=[axisY, axisX])
        
        g = f[0]
        g.squeeze(copy=False)
#        g.standard_name = 'ancillary2'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryB'
        f.insert_field_ancillary(anc, axes=[axisX])

        g = f[..., 0]
        g = g.squeeze()
#        g.standard_name = 'ancillary3'
#        g *= 0.001
        anc = cfdm.FieldAncillary(data=g.data)
        anc.standard_name = 'ancillaryC'
        f.insert_field_ancillary(anc, axes=[axisY])

        
        f.setprop('flag_values', numpy.array([1, 2, 4], 'int32'))
        f.setprop('flag_meanings', 'a bb ccc')
        f.setprop('flag_masks', [2, 1, 0])

        print repr(f.getprop('flag_meanings'))
        print 'F masks', repr(f.getprop('flag_masks'))
        print repr(f.getprop('flag_values'))

        for cm in cfdm.CellMethod.parse(axisX+': mean '+axisY+': max'):
            f.insert_cell_method(cm)


        print f
        print f.constructs()
        print f.construct_axes()
        
        print 'f.constructs()[ref1]._coordinates =', f.constructs()[ref1]._coordinates
        
        f.dump()
#        print f
        # Write the file, and read it in
#        print f.shape
 
#        print 'MADE:'
#        print f.Items._axes
#        print '============================'
        cfdm.write(f, self.filename, fmt='NETCDF3_CLASSIC',_debug=True)

        g = cfdm.read(self.filename, _debug=True) #, squeeze=True)
#        g[0].dump()
#        print '\n GGGG =============================================='
#        print f
#        print g
#        r =    g[0].item('atmos', role='r')
#        print  r.items()
#        print g.dump()
#        print 'GGGG =============================================='



        self.assertTrue(len(g) == 1)

        g = g[0].squeeze(copy=False)
        
        
        #        print f
##        print g
#        print f.items()
#        f.dump()
        g.dump()




        print repr(g.getprop('flag_meanings'))
        print 'G MASKS', repr(g.getprop('flag_masks'))
        print repr(g.getprop('flag_values'))
        print g.properties()
        
        self.assertTrue(sorted(f.constructs().keys()) ==  sorted(g.constructs().keys()))

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
