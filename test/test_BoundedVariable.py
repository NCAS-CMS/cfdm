import datetime
import os
import time 
import unittest

import numpy

import cfdm

class BoundedVariableTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        self.chunk_sizes = (17, 34, 300, 100000)[::-1]
        

#--- End: class

if __name__ == "__main__":
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print ''
    unittest.main(verbosity=2)
