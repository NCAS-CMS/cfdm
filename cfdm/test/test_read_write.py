from __future__ import print_function
from builtins import (range, str)

import datetime
import tempfile
import os
import platform
import unittest
import atexit
import inspect
import subprocess
import numpy

import cfdm

warnings = False

tmpfile = tempfile.mktemp('.cfdm_test')
tmpfileh = tempfile.mktemp('.cfdm_test')
tmpfileh2 = tempfile.mktemp('.cfdm_test')
tmpfilec = tempfile.mktemp('.cfdm_test')
tmpfile0 = tempfile.mktemp('.cfdm_test')
tmpfile1 = tempfile.mktemp('.cfdm_test')
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

        self.string_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'string_char.nc')

        self.test_only = []
        # self.test_only = ['NOTHING!!!!!']
        # self.test_only = ['test_read_CDL']
        # self.test_only = ['test_write_filename']
        # self.test_only = ['test_read_write_unlimited']
        # self.test_only = ['test_read_field']
        # self.test_only = ['test_read_mask']
        # self.test_only = ['test_read_write_format']
        # self.test_only = ['test_read_write_Conventions']

    def test_write_filename(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        tmpfile = tempfile.mktemp('.cfdm_test')
        tmpfiles.append(tmpfile)

        tmpfile = 'delme.nc'

        f = cfdm.example_field(0)
        a = f.data.array

        cfdm.write(f, tmpfile)
        g = cfdm.read(tmpfile)

        with self.assertRaises(Exception):
            cfdm.write(g, tmpfile)

        self.assertTrue((a == g[0].data.array).all())

    def test_read_field(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Test field keyword of cfdm.read
        filename = self.filename

        f = cfdm.read(filename)
        self.assertTrue(len(f) == 1, '\n'+str(f))

        f = cfdm.read(filename, extra=['dimension_coordinate'],
                      warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, extra=['auxiliary_coordinate'],
                      warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, extra='cell_measure')
        self.assertTrue(len(f) == 2, '\n'+str(f))

        f = cfdm.read(filename, extra=['field_ancillary'])
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, extra='domain_ancillary', warnings=warnings)
        self.assertTrue(len(f) == 4, '\n'+str(f))

        f = cfdm.read(filename, extra=['field_ancillary',
                                       'auxiliary_coordinate'],
                      warnings=warnings)
        self.assertTrue(len(f) == 7, '\n'+str(f))

        self.assertTrue(len(cfdm.read(filename,
                                      extra=['domain_ancillary',
                                             'auxiliary_coordinate'],
                                      warnings=warnings)) == 7)
        self.assertTrue(len(cfdm.read(filename,
                                      extra=['domain_ancillary',
                                             'cell_measure',
                                             'auxiliary_coordinate'],
                                      warnings=warnings)) == 8)

        f = cfdm.read(filename, extra=('field_ancillary',
                                       'dimension_coordinate',
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
            self.assertTrue(f.equals(g, verbose=3),
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
                        f.equals(g, verbose=3),
                        "Bad read/write with lossless compression: "
                        "{}, {}, {}".format(fmt, compress, shuffle))
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
            self.assertTrue(f.equals(g, verbose=3),
                            'Bad read/write of format: {}'.format(fmt))

    def test_read_mask(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.example_field(0)

        N = f.size

        f.data[1, 1] = cfdm.masked
        f.data[2, 2] = cfdm.masked

        f.del_property('_FillValue', None)
        f.del_property('missing_value', None)

        cfdm.write(f, tmpfile)

        g = cfdm.read(tmpfile)[0]
        self.assertTrue(numpy.ma.count(g.data.array) == N - 2)

        g = cfdm.read(tmpfile, mask=False)[0]
        self.assertTrue(numpy.ma.count(g.data.array) == N)

        g.apply_masking(inplace=True)
        self.assertTrue(numpy.ma.count(g.data.array) == N - 2)

        f.set_property('_FillValue', 999)
        f.set_property('missing_value', -111)
        cfdm.write(f, tmpfile)

        g = cfdm.read(tmpfile)[0]
        self.assertTrue(numpy.ma.count(g.data.array) == N - 2)

        g = cfdm.read(tmpfile, mask=False)[0]
        self.assertTrue(numpy.ma.count(g.data.array) == N)

        g.apply_masking(inplace=True)
        self.assertTrue(numpy.ma.count(g.data.array) == N - 2)

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
        subprocess.run(
            ' '.join(['ncdump', '-h', self.filename, '>', tmpfileh]),
                                shell=True, check=True)
        subprocess.run(
            ' '.join(['ncdump', '-c', self.filename, '>', tmpfilec]),
                       shell=True, check=True)

        f0 = cfdm.read(self.filename)[0]
        f = cfdm.read(tmpfile)[0]
        h = cfdm.read(tmpfileh)[0]
        c = cfdm.read(tmpfilec)[0]

        self.assertTrue(f0.equals(f, verbose=3))

        self.assertTrue(f.construct('grid_latitude').equals(
            c.construct('grid_latitude'), verbose=3))
        self.assertTrue(f0.construct('grid_latitude').equals
                        (c.construct('grid_latitude'), verbose=3))

        with self.assertRaises(OSError):
            x = cfdm.read('test_read_write.py')

        # TODO: make portable instead of skipping on Mac OS (see Issue #25):
        #       '-i' aspect solved, but the regex patterns need amending too.
        if platform.system() != 'Darwin':  # False for Mac OS(X) only
            for regex in [
                r'"1 i\ \ "',
                r'"1 i\// comment"',
                r'"1 i\ // comment"',
                r'"1 i\ \t// comment"'
            ]:
                # Note that really we just want to do an in-place sed
                # ('sed -i') but because of subtle differences between the
                # GNU (Linux OS) and BSD (some Mac OS) command variants a
                # safe portable one-liner may not be possible. This will
                # do, overwriting the intermediate file. The '-E' to mark
                # as an extended regex is also for portability.
                subprocess.run(
                    ' '.join(
                        ['sed', '-E', '-e', regex, tmpfileh, '>' + tmpfileh2,
                         '&&', 'mv', tmpfileh2, tmpfileh]
                    ), shell=True, check=True
                )

                h = cfdm.read(tmpfileh)[0]

#        subprocess.run(' '.join(['head', tmpfileh]),  shell=True, check=True)

    def test_read_write_string(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.string_filename)

        n = int(len(f)/2)

        for i in range(0, n):
            j = i + n
            self.assertTrue(f[i].data.equals(f[j].data, verbose=3),
                            "{!r} {!r}".format(f[i], f[j]))
            self.assertTrue(f[j].data.equals(f[i].data, verbose=3),
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

                        for i, j in zip(cfdm.read(tmpfile1),
                                        cfdm.read(tmpfile0)):
                            self.assertTrue(i.equals(j, verbose=3))
        #--- End: for

    def test_read_write_Conventions(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)[0]

        version = 'CF-' + cfdm.CF()
        other = 'ACDD-1.3'

        for Conventions in (other,):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertTrue(
                g.get_property('Conventions') == ' '.join([version, other]),
                "{!r}, {!r}".format(
                    g.get_property('Conventions'), Conventions))

        for Conventions in (version,
                            '',
                            ' ',
                            ',',
                            ', ',
                            ):
            Conventions = version
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertTrue(g.get_property('Conventions') == version,
                            "{!r}, {!r}".format(
                                g.get_property('Conventions'),
                                Conventions))

        for Conventions in ([version],                          
                            [version, other],
        ):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertTrue(
                g.get_property('Conventions') == ' '.join(Conventions),
                "{!r}, {!r}".format(
                    g.get_property('Conventions'), Conventions))

        for Conventions in ([other, version],):
            cfdm.write(f, tmpfile0, Conventions=Conventions)
            g = cfdm.read(tmpfile0)[0]
            self.assertTrue(
                g.get_property('Conventions') == ' '.join([version, other]),
                "{!r}, {!r}".format(
                    g.get_property('Conventions'), Conventions))

#--- End: class

if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
