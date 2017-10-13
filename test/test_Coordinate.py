import datetime
import os
import time 
import unittest

import numpy

import cfdm

class CoordinateTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

#    def test_convert_reference_time(self):
#        c = cf.DimensionCoordinate(data=cf.Data([1, 3], 'months since 2000-1-1'),
#                                   bounds=cf.Data([[0, 2], [2, 4]]))
#     
#        self.assertTrue((c.dtarray == 
#                         numpy.array([cf.dt(2000, 1, 31, 10, 29, 3),
#                                      cf.dt(2000, 4, 1, 7, 27, 11)])).all(),
#                        'c.dtarray={}'.format(c.dtarray))
#
#        c.convert_reference_time(calendar_months=True, i=True)
#        self.assertTrue((c.dtarray ==
#                         numpy.array([cf.dt(2000, 2, 1, 0, 0),
#                                      cf.dt(2000, 4, 1, 0, 0)])).all(),
#                        'c.dtarray={}'.format(c.dtarray))
#
#        self.assertTrue((c.bounds.dtarray == 
#                         numpy.array([[cf.dt(2000, 1, 1, 0, 0), cf.dt(2000, 3, 1, 0, 0)],
#                                      [cf.dt(2000, 3, 1, 0, 0), cf.dt(2000, 5, 1, 0, 0)]])).all(),
#                        'c.bounds.dtarray={}'.format(c.bounds.dtarray))
#    #--- End: def

#--- End: class

if __name__ == "__main__":
    print 'Run date:', datetime.datetime.now()
    print cfdm.environment()
    print ''
    unittest.main(verbosity=2)
