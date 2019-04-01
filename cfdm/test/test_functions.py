from __future__ import print_function
import datetime
import inspect
import unittest

import cfdm

class FunctionsTest(unittest.TestCase):
    def setUp(self):
        self.test_only = []
    #--- End: def
        
    def test_CF_ATOL_RTOL_environment(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertTrue(cfdm.CF() == '1.7')

        org = cfdm.RTOL()
        self.assertTrue(cfdm.RTOL(1e-5) == org)
        self.assertTrue(cfdm.RTOL() == 1e-5)
        self.assertTrue(cfdm.RTOL(org) == 1e-5)
        self.assertTrue(cfdm.RTOL() == org)
        
        org = cfdm.ATOL()
        self.assertTrue(cfdm.ATOL(1e-5) == org)
        self.assertTrue(cfdm.ATOL() == 1e-5)
        self.assertTrue(cfdm.ATOL(org) == 1e-5)
        self.assertTrue(cfdm.ATOL() == org)

        out = cfdm.environment(display=False)
    #--- End: def
    
#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)
