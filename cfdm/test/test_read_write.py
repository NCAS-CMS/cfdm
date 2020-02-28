from __future__ import print_function
from builtins import (range, str)

import datetime
import tempfile
import os
import unittest
import atexit
import inspect
import subprocess
import numpy

import cfdm

warnings = False

tmpfile  = tempfile.mktemp('.cfdm_test')
tmpfileh  = tempfile.mktemp('.cfdm_test')
tmpfilec  = tempfile.mktemp('.cfdm_test')
tmpfile0  = tempfile.mktemp('.cfdm_test')
tmpfile1  = tempfile.mktemp('.cfdm_test')
tmpfiles = [tmpfile, tmpfileh, tmpfilec, tmpfile0, tmpfile1]
def _remove_tmpfiles():
    '''
    '''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass

        
atexit.register(_remove_tmpfiles)


class read_writeTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    string_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'string_char.nc')

    test_only = []
#    test_only = ['NOTHING!!!!!']
#    test_only = ['test_read_CDL']
#    test_only = ['test_write_HDF_chunks']
#    test_only = ['test_read_write_unlimited']
#    test_only = ['test_read_field']
#    test_only = ['test_read_write_string']
#    test_only = ['test_read_write_format']
    
    def test_read_field(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Test field keyword of cfdm.read
        filename = self.filename
        
        f = cfdm.read(filename)
        self.assertTrue(len(f) == 1, '\n'+str(f))

        f = cfdm.read(filename, extra=['dimension_coordinate'], warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, extra=['auxiliary_coordinate'], warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))
        
        f = cfdm.read(filename, extra='cell_measure')
        self.assertTrue(len(f) == 2, '\n'+str(f))

        f = cfdm.read(filename, extra=['field_ancillary'])
        self.assertTrue(len(f) == 4, '\n'+str(f))
                
        f = cfdm.read(filename, extra='domain_ancillary', warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))
        
        f = cfdm.read(filename, extra=['field_ancillary', 'auxiliary_coordinate'],
                      warnings=warnings)
        self.assertTrue(len(f) == 7, '\n'+str(f))
        
        self.assertTrue(len(cfdm.read(filename, extra=['domain_ancillary', 'auxiliary_coordinate'], warnings=warnings)) == 7)
        self.assertTrue(len(cfdm.read(filename, extra=['domain_ancillary', 'cell_measure', 'auxiliary_coordinate'], warnings=warnings)) == 8)

        f = cfdm.read(filename, extra=('field_ancillary', 'dimension_coordinate',
                                       'cell_measure', 'auxiliary_coordinate',
                                       'domain_ancillary'), warnings=warnings)
        self.assertTrue(len(f) == 14, '\n'+str(f))


    def test_read_write_format(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        for fmt in ('NETCDF3_CLASSIC',
                    'NETCDF3_64BIT',
                    'NETCDF3_64BIT_OFFSET',
                    'NETCDF3_64BIT_DATA',
                    'NETCDF4',
                    'NETCDF4_CLASSIC',):
            cfdm.write(f, tmpfile, fmt=fmt)
            g = cfdm.read(tmpfile)
            self.assertTrue(len(g) == 1, 'g = '+repr(g))
            g = g[0]
            self.assertTrue(f.equals(g, verbose=True),
                            'Bad read/write of format: {}'.format(fmt))
            

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
                        f.equals(g, verbose=True),
                        'Bad read/write with lossless compression: {}, {}, {}'.format(fmt, compress, shuffle))
        #--- End: for


    def test_read_write_missing_data(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]
        for fmt in ('NETCDF3_CLASSIC',
                    'NETCDF3_64BIT',
                    'NETCDF3_64BIT_OFFSET',
                    'NETCDF3_64BIT_DATA',
                    'NETCDF4',
                    'NETCDF4_CLASSIC'):
            cfdm.write(f, tmpfile, fmt=fmt)
            g = cfdm.read(tmpfile)[0]
            self.assertTrue(f.equals(g, verbose=True),
                            'Bad read/write of format: {}'.format(fmt))


    def test_write_datatype(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0] 
        self.assertTrue(f.data.dtype == numpy.dtype(float))

        f.set_property('_FillValue'   , numpy.float64(-999.))
        f.set_property('missing_value', numpy.float64(-999.))
        
        cfdm.write(f, tmpfile, fmt='NETCDF4', 
                 datatype={numpy.dtype(float): numpy.dtype('float32')})
        g = cfdm.read(tmpfile)[0]
        self.assertTrue(g.data.dtype == numpy.dtype('float32'), 
                        'datatype read in is '+str(g.data.dtype))


    def test_read_write_unlimited(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        for fmt in ('NETCDF4',
                    'NETCDF4_CLASSIC',
                    'NETCDF3_CLASSIC',
                    'NETCDF3_64BIT',
                    'NETCDF3_64BIT_OFFSET',
                    'NETCDF3_64BIT_DATA'):
            f = cfdm.read(self.filename)[0]
            
            f.domain_axes['domainaxis0'].nc_set_unlimited(True)
            cfdm.write(f, tmpfile, fmt=fmt)
            
            f = cfdm.read(tmpfile)[0]
            self.assertTrue(f.domain_axes['domainaxis0'].nc_is_unlimited())

        fmt = 'NETCDF4'
        f = cfdm.read(self.filename)[0]
        f.domain_axes['domainaxis0'].nc_set_unlimited(True)
        f.domain_axes['domainaxis2'].nc_set_unlimited(True)
        cfdm.write(f, tmpfile, fmt=fmt)
        
        f = cfdm.read(tmpfile)[0]
        self.assertTrue(f.domain_axes['domainaxis0'].nc_is_unlimited())
        self.assertTrue(f.domain_axes['domainaxis2'].nc_is_unlimited())


    def test_read_CDL(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        subprocess.run(' '.join(['ncdump', self.filename, '>', tmpfile]),
                       shell=True, check=True)
        subprocess.run(' '.join(['ncdump', '-h', self.filename, '>', tmpfileh]),
                                shell=True, check=True)
        subprocess.run(' '.join(['ncdump', '-c', self.filename, '>', tmpfilec]),
                       shell=True, check=True)

        f0 = cfdm.read(self.filename)[0]
        f = cfdm.read(tmpfile)[0]
        h = cfdm.read(tmpfileh)[0]
        c = cfdm.read(tmpfilec)[0]

        self.assertTrue(f0.equals(f, verbose=True))

        self.assertTrue(f.construct('grid_latitude').equals(c.construct('grid_latitude'), verbose=True))
        self.assertTrue(f0.construct('grid_latitude').equals(c.construct('grid_latitude'), verbose=True))

        with self.assertRaises(OSError):
            x = cfdm.read('test_read_write.py')
            
        subprocess.run(' '.join(['sed', '-i', r'"1 i\ \ "', tmpfileh]),
                       shell=True, check=True)
        h = cfdm.read(tmpfileh)[0]
        
        subprocess.run(' '.join(['sed', '-i', r'"1 i\// comment"', tmpfileh]),
                       shell=True, check=True)
        h = cfdm.read(tmpfileh)[0]

        subprocess.run(' '.join(['sed', '-i', r'"1 i\ // comment"', tmpfileh]),
                       shell=True, check=True)
        h = cfdm.read(tmpfileh)[0]

        subprocess.run(' '.join(['sed', '-i', r'"1 i\ \t// comment"', tmpfileh]),
                       shell=True, check=True)
        h = cfdm.read(tmpfileh)[0]

#        subprocess.run(' '.join(['head', tmpfileh]),  shell=True, check=True)

            
    def test_read_write_string(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.string_filename)

        n = int(len(f)/2)
        
        for i in range(0, n):
            j = i + n
            self.assertTrue(f[i].data.equals(f[j].data, verbose=1),
                            "{!r} {!r}".format(f[i], f[j]))
            self.assertTrue(f[j].data.equals(f[i].data, verbose=1),
                            "{!r} {!r}".format(f[j], f[i]))


        for string0 in (True, False):
            for fmt0 in ('NETCDF4',
                         'NETCDF3_CLASSIC',
                         'NETCDF4_CLASSIC',
                         'NETCDF3_64BIT',
                         'NETCDF3_64BIT_OFFSET',
                         'NETCDF3_64BIT_DATA'):
                f0 = cfdm.read(self.string_filename)
                cfdm.write(f0, tmpfile0, fmt=fmt0, string=string0)
                
                for string1 in (True, False):
                    for fmt1 in ('NETCDF4',
                                 'NETCDF3_CLASSIC',
                                 'NETCDF4_CLASSIC',
                                 'NETCDF3_64BIT',
                                 'NETCDF3_64BIT_OFFSET',
                                 'NETCDF3_64BIT_DATA'):
                        f1 = cfdm.read(self.string_filename)
                        cfdm.write(f0, tmpfile1, fmt=fmt1, string=string1)
    
                        for i, j in zip(cfdm.read(tmpfile1), cfdm.read(tmpfile0)):
                            self.assertTrue(i.equals(j, verbose=1))
        #--- End: for
        
                
#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
