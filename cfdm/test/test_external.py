import atexit
import datetime
import os
import tempfile
import time
import unittest

import netCDF4
import numpy

import cfdm


n_tmpfiles = 3
tmpfiles = [tempfile.mktemp('_test_external.nc', dir=os.getcwd())
            for i in range(n_tmpfiles)]
(
    tempfile,
    tempfile_parent,
    tempfile_external,
) = tmpfiles


def _remove_tmpfiles():
    '''Remove temporary files created during tests.

    '''
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class ExternalVariableTest(unittest.TestCase):
    def setUp(self):
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL('DISABLE')
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.parent_file = 'parent.nc'
        self.external_file = 'external.nc'
        self.combined_file = 'combined.nc'
        self.external_missing_file = 'external_missing.nc'

        self.test_only = []

    def test_EXTERNAL_READ(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Read the parent file on its own, without the external file
        f = cfdm.read(self.parent_file)

        for i in f:
            _ = repr(i)
            _ = str(i)
            self.assertIsInstance(i.dump(display=False), str)

        self.assertEqual(len(f), 1)
        f = f[0]

        cell_measure = f.constructs.filter_by_identity('measure:area').value()

        self.assertTrue(cell_measure.nc_get_external())
        self.assertEqual(cell_measure.nc_get_variable(), 'areacella')
        self.assertEqual(cell_measure.properties(), {})
        self.assertFalse(cell_measure.has_data())

        # External file contains only the cell measure variable
        f = cfdm.read(self.parent_file, external=[self.external_file],
                      verbose=False)

        c = cfdm.read(self.combined_file, verbose=False)

        for i in c + f:
            _ = repr(i)
            _ = str(i)
            self.assertIsInstance(i.dump(display=False), str)

        cell_measure = f[0].constructs.filter_by_identity(
            'measure:area').value()

        self.assertEqual(len(f), 1)
        self.assertEqual(len(c), 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], verbose=3))

        # External file contains other variables
        f = cfdm.read(self.parent_file, external=self.combined_file,
                      verbose=False)

        for i in f:
            _ = repr(i)
            _ = str(i)
            self.assertIsInstance(i.dump(display=False), str)

        self.assertEqual(len(f), 1)
        self.assertEqual(len(c), 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], verbose=3))

        # Two external files
        f = cfdm.read(
            self.parent_file,
            external=[self.external_file, self.external_missing_file],
            verbose=False
        )

        for i in f:
            _ = repr(i)
            _ = str(i)
            self.assertIsInstance(i.dump(display=False), str)

        self.assertEqual(len(f), 1)
        self.assertEqual(len(c), 1)

        for i in range(len(f)):
            self.assertTrue(c[i].equals(f[i], verbose=3))

    def test_EXTERNAL_WRITE(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        parent = cfdm.read(self.parent_file)
        combined = cfdm.read(self.combined_file)

        # External file contains only the cell measure variable
        f = cfdm.read(self.parent_file, external=self.external_file)

        cfdm.write(f, tempfile)
        g = cfdm.read(tempfile)

        self.assertEqual(len(g), len(combined))

        for i in range(len(g)):
            self.assertTrue(combined[i].equals(g[i], verbose=3))

        cell_measure = g[0].constructs('measure:area').value()

        self.assertFalse(cell_measure.nc_get_external())
        cell_measure.nc_set_external(True)
        self.assertTrue(cell_measure.nc_get_external())
        self.assertTrue(cell_measure.properties())
        self.assertTrue(cell_measure.has_data())

        self.assertTrue(
            g[0].constructs.filter_by_identity(
                'measure:area').value().nc_get_external()
        )

        cfdm.write(g, tempfile_parent,
                   external=tempfile_external,
                   verbose=False)

        h = cfdm.read(tempfile_parent, verbose=False)

        self.assertEqual(len(h), len(parent))

        for i in range(len(h)):
            self.assertTrue(parent[i].equals(h[i], verbose=3))

        h = cfdm.read(tempfile_external)
        external = cfdm.read(self.external_file)

        self.assertEqual(len(h), len(external))

        for i in range(len(h)):
            self.assertTrue(external[i].equals(h[i], verbose=3))


# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment(display=False)
    print()
    unittest.main(verbosity=2)
