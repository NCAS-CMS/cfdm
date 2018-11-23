from __future__ import print_function
import datetime
import inspect
import unittest

import cfdm

class FunctionsTest(unittest.TestCase):
    def setUp(self):
        self.test_only = []
    #--- End: def
        
    def test_CF(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        self.assertTrue(cfdm.CF() == '1.7')
    #--- End: def
    
#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
