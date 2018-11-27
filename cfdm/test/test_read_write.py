from __future__ import print_function
from builtins import (range, str)

import datetime
import tempfile
import os
import unittest
import atexit
import inspect

import numpy

import cfdm

tmpfile  = tempfile.mktemp('.cf-python_test')
tmpfiles = [tmpfile]
def _remove_tmpfiles():
    '''
'''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass
#--- End: def
atexit.register(_remove_tmpfiles)

class read_writeTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    test_only = []
#    test_only = ['NOTHING!!!!!']
#    test_only = ['test_write_HDF_chunks']
#    test_only = ['test_read_write_unlimited']
#    test_only = ['test_read_field']
#    test_only = ['test_write_datatype']
    
    def test_read_field(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Test field keyword of cfdm.read
        filename = self.filename
        
        f = cfdm.read(filename)
        self.assertTrue(len(f) == 1, '\n'+str(f))

        f = cfdm.read(filename, create_field=['dimension_coordinate'])
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, create_field=['auxiliary_coordinate'])
        self.assertTrue(len(f) == 4, '\n'+str(f))
        
        f = cfdm.read(filename, create_field='cell_measure')
        self.assertTrue(len(f) == 2, '\n'+str(f))

        f = cfdm.read(filename, create_field=['field_ancillary'])
        self.assertTrue(len(f) == 4, '\n'+str(f))
                
        f = cfdm.read(filename, create_field='domain_ancillary')
        self.assertTrue(len(f) == 4, '\n'+str(f))
        
        f = cfdm.read(filename, create_field=['field_ancillary', 'auxiliary_coordinate'])
        self.assertTrue(len(f) == 7, '\n'+str(f))
        
        self.assertTrue(len(cfdm.read(filename, create_field=['domain_ancillary', 'auxiliary_coordinate'])) == 7)
        self.assertTrue(len(cfdm.read(filename, create_field=['domain_ancillary', 'cell_measure', 'auxiliary_coordinate'])) == 8)

        f = cfdm.read(filename, create_field=('field_ancillary', 'dimension_coordinate',
                                       'cell_measure', 'auxiliary_coordinate',
                                       'domain_ancillary'))
        self.assertTrue(len(f) == 14, '\n'+str(f))
    #--- End: def

    def test_read_write_format(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        for fmt in ('NETCDF3_CLASSIC',
                    'NETCDF3_64BIT',
                    'NETCDF4',
                    'NETCDF4_CLASSIC'):
            cfdm.write(f, tmpfile, fmt=fmt)
            g = cfdm.read(tmpfile)[0]
            self.assertTrue(f.equals(g, traceback=True),
                            'Bad read/write of format: {}'.format(fmt))
        #--- End: for
    #--- End: def

    def test_read_write_netCDF4_compress_shuffle(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        for fmt in ('NETCDF4',
                    'NETCDF4_CLASSIC'):
            for shuffle in (True, False):
                for compress in range(10):
                    cfdm.write(f, tmpfile, fmt=fmt,
                               compress=compress,
                               shuffle=shuffle)
                    g = cfdm.read(tmpfile)[0]
                    self.assertTrue(
                        f.equals(g, traceback=True),
                        'Bad read/write with lossless compression: {}, {}, {}'.format(fmt, compress, shuffle))
        #--- End: for
    #--- End: def

    def test_write_datatype(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0] 
        self.assertTrue(f.data.dtype == numpy.dtype(float))

        cfdm.write(f, tmpfile, fmt='NETCDF4', 
                 datatype={numpy.dtype(float): numpy.dtype('float32')})
        g = cfdm.read(tmpfile)[0]
        self.assertTrue(g.data.dtype == numpy.dtype('float32'), 
                        'datatype read in is '+str(g.data.dtype))
    #--- End: def

#    def test_write_HDF_chunks(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#            
#        for fmt in ('NETCDF3_CLASSIC', 'NETCDF4'):
#            f = cfdm.read(self.filename)[0]
#            f.HDF_chunks({'T': 10000, 1: 3, 'grid_lat': 222, 45:45})
#            cfdm.write(f, tmpfile, fmt=fmt, HDF_chunksizes={'X': 6})
#        #--- End: for
#    #--- End: def

#    def test_read_write_unlimited(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#        f = cfdm.read(self.filename)[0]
#
#        fmt = 'NETCDF4'
#        for axis in ('atmosphere_hybrid_height_coordinate', 'X', 'Y'):
#            org = f.unlimited({axis: True})
#            cfdm.write(f, tmpfile, fmt=fmt)
#            f.unlimited(org)
#            
#            g = cfdm.read(tmpfile)[0]
#            self.assertTrue(g.unlimited()[g.axis(axis, key=True)] is True,
#                            'Failed with axis={}, fmt={}'.format(axis, fmt))
#
#        fmt = 'NETCDF3_CLASSIC'
#        for axis in ('atmosphere_hybrid_height_coordinate',):
#            org = f.unlimited({axis: True})
#            cfdm.write(f, tmpfile, fmt=fmt)
#            f.unlimited(org)
#            
#            g = cfdm.read(tmpfile)[0]
#            self.assertTrue(g.unlimited()[g.axis(axis, key=True)] is True,
#                            'Failed with axis={}, fmt={}'.format(axis, fmt))
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({'Y': True, 'X': True})
#        cfdm.write(f, tmpfile, fmt=fmt)
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(g.unlimited()[g.axis('X', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#        self.assertTrue(g.unlimited()[g.axis('Y', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('Y', fmt))
#
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({'X': False})
#        cfdm.write(f, tmpfile, fmt=fmt, unlimited=['X'])
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(not g.unlimited()[g.axis('X', key=True)],
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({'X': True})
#        cfdm.write(f, tmpfile, fmt=fmt, unlimited=['X'])
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(g.unlimited()[g.axis('X', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({'Y': True})
#        cfdm.write(f, tmpfile, fmt=fmt, unlimited=['X'])
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(g.unlimited()[g.axis('X', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#        self.assertTrue(g.unlimited()[g.axis('Y', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('Y', fmt))
#
# 
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({('X', 'Y'): True})
#        cfdm.write(f, tmpfile, fmt=fmt)
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(g.unlimited()[g.axis('X', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#        self.assertTrue(g.unlimited()[g.axis('Y', key=True)] is True,
#                        'Failed with axis={}, fmt={}'.format('Y', fmt))
#
# 
#
#        fmt = 'NETCDF4'
#        org = f.unlimited({('X', 'Y'): True})
#        f.unlimited(None)
#        cfdm.write(f, tmpfile, fmt=fmt)
#        f.unlimited(org)
#
#        g = cfdm.read(tmpfile)[0]
#        self.assertTrue(not g.unlimited()[g.axis('X', key=True)],
#                        'Failed with axis={}, fmt={}'.format('X', fmt))
#        self.assertTrue(not g.unlimited()[g.axis('Y', key=True)],
#                        'Failed with axis={}, fmt={}'.format('Y', fmt))
#    #--- End: def

#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
