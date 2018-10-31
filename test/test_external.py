from __future__ import print_function
import datetime
import os
import time 
import unittest

import netCDF4
import numpy

import cfdm

class ExternalVariableTest(unittest.TestCase):
    def setUp(self):
        (self.parent_file,
         self.external_file,
         self.combined_file,
         self.external_missing_file) = self._make_files()
        
        self.test_only = []
    #--- End: def
    
    def test_EXTERNAL(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # External file contains only the cell measure variable
        f = cfdm.read(self.parent_file,
                      external_files=[self.external_file],
                      _debug=False)

        c = cfdm.read(self.combined_file, _debug=False)

#        print ('\nParent + External:\n')
#        for x in f:
#            print(x)
##            print (x.get_read_report())
#
#        print ('\nCombined:\n')
#        for x in c:
#            print(x)

        self.assertTrue(len(f) == 1)
        self.assertTrue(len(c) == 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], traceback=True))

        # External file contains other variables
        f = cfdm.read(self.parent_file,
                      external_files=self.combined_file,
                      _debug=False)

#        print ('\nParent + Combined:\n')
#        for x in f:
#            print(x)
#
#        print ('\nCombined:\n')
#        for x in c:
#            print(x)

        self.assertTrue(len(f) == 1)
        self.assertTrue(len(c) == 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], traceback=True))

        # Two external files
        f = cfdm.read(self.parent_file,
                      external_files=[self.external_file, self.external_missing_file],
                      _debug=False)

#        print ('\nParent + External + External Missing:\n')
#        for x in f:
#            print(x)
#
#        print ('\nCombined:\n')
#        for x in c:
#            print(x)

        self.assertTrue(len(f) == 1)
        self.assertTrue(len(c) == 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], traceback=True))
    #--- End: def        

    def _make_files(self):
        def _pp(filename, parent=False, external=False, combined=False, external_missing=False):
            '''
            '''
            nc = netCDF4.Dataset(filename, 'w', format='NETCDF3_CLASSIC')
            
            nc.createDimension('grid_latitude', 10)
            nc.createDimension('grid_longitude', 9)

            nc.Conventions = 'CF-1.7'
            if parent:
                nc.external_variables = 'areacella'

            if parent or combined or external_missing:
                grid_latitude = nc.createVariable(dimensions=('grid_latitude',),
                                                  datatype='f8',
                                                  varname='grid_latitude')
                grid_latitude.setncatts({'units': 'degrees', 'standard_name': 'grid_latitude'})
                grid_latitude[...] = range(10)
                
                grid_longitude = nc.createVariable(dimensions=('grid_longitude',),
                                                   datatype='f8',
                                                   varname='grid_longitude')
                grid_longitude.setncatts({'units': 'degrees', 'standard_name': 'grid_longitude'})
                grid_longitude[...] = range(9)
                
                latitude = nc.createVariable(dimensions=('grid_latitude', 'grid_longitude'),
                                             datatype='i4',
                                             varname='latitude')
                latitude.setncatts({'units': 'degree_N', 'standard_name': 'latitude'})
                
                latitude[...] = numpy.arange(90).reshape(10, 9)
                
                longitude = nc.createVariable(dimensions=('grid_longitude', 'grid_latitude'),
                                              datatype='i4',
                                              varname='longitude')
                longitude.setncatts({'units': 'degreeE', 'standard_name': 'longitude'})
                longitude[...] = numpy.arange(90).reshape(9, 10)
                
                eastward_wind = nc.createVariable(dimensions=('grid_latitude', 'grid_longitude'),
                                                  datatype='f8',
                                                  varname=u'eastward_wind')
#                eastward_wind.setncatts({'coordinates': u'latitude longitude', 'standard_name': 'eastward_wind', 'cell_methods': 'grid_longitude: mean (interval: 1 day comment: ok) grid_latitude: maximum where sea', 'cell_measures': 'area: areacella', 'units': 'm s-1'})
                eastward_wind.coordinates = u'latitude longitude'
                eastward_wind.standard_name = 'eastward_wind'
                eastward_wind.cell_methods = 'grid_longitude: mean (interval: 1 day comment: ok) grid_latitude: maximum where sea'
                eastward_wind.cell_measures = 'area: areacella'
                eastward_wind.units = 'm s-1'
                eastward_wind[...] = numpy.arange(90).reshape(10, 9) - 45.5

            if external or combined:                
                areacella = nc.createVariable(dimensions=('grid_longitude', 'grid_latitude'),
                                              datatype='f8',
                                              varname='areacella')
                areacella.setncatts({'units': 'm2', 'measure': 'area'})
                areacella[...] = numpy.arange(90).reshape(9, 10) + 100000.5
                
            nc.close
        #--- End: def

        parent_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'parent.nc')        
        external_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'external.nc')            
        combined_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'combined.nc')        
        external_missing_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             'external_missing.nc')            
        
        _pp(parent_file  , parent=True)
        _pp(external_file, external=True)
        _pp(combined_file, combined=True)
        _pp(external_missing_file, combined=True)

        return parent_file, external_file, combined_file, external_missing_file
    #--- End: def
    
#--- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)

