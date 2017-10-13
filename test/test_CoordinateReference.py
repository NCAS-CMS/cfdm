import datetime
import os
import unittest

import numpy

import cfdm

class CoordinateReferenceTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')

    def test_CoordinateReference_equals(self):
        f = cfdm.read(self.filename)[0]
        
        t = cfdm.CoordinateReference(name='atmosphere_hybrid_height_coordinate',
                                   ancillaries={'a': 'aux0', 'b': 'aux1', 'orog': 'orog'})
        self.assertTrue(t.equals(t.copy(), traceback=True))
        
        # Create a rotated_latitude_longitude grid mapping coordinate
        # reference
        t = cfdm.CoordinateReference(name='rotated_latitude_longitude',
                                   parameters={'grid_north_pole_latitude': 38.0,
                                               'grid_north_pole_longitude': 190.0})
        self.assertTrue(t.equals(t.copy(), traceback=True))

        t = cfdm.CoordinateReference(name='rotated_latitude_longitude',
                                   coordinates=('coord1', 'coord2'),
                                   parameters={'grid_north_pole_latitude': 38.0,
                                               'grid_north_pole_longitude': 190.0},
                                   ancillaries={'a': 'aux0', 'b': 'aux1', 'orog': 'orog'})
        self.assertTrue(t.equals(t.copy(), traceback=True))
    #--- End: def

    def test_Field_ref_refs(self):
        f = cfdm.read(self.filename)[0]
        
        self.assertTrue(f.item('BLAH',  role='r') is None)
        self.assertTrue(f.item('atmos', role='r', key=True) == 'ref0')
        self.assertTrue(f.item('atmos', role='r', key=True, inverse=True) == 'ref1')

        self.assertTrue(set(f.items(role='r')) == set(['ref0', 'ref1']))
        self.assertTrue(set(f.items('BLAH', role='r')) == set())
        self.assertTrue(set(f.items('rot', role='r')) == set(['ref1']))
        self.assertTrue(set(f.items('rot', role='r', inverse=True)) == set(['ref0']))
        self.assertTrue(set(f.items('atmosphere_hybrid_height_coordinate', role='r', exact=True)) == set(['ref0']))
    #--- End: def
#--- End: class

if __name__ == '__main__':
    print 'Run date:', datetime.datetime.now()
    print cfdm.environment()
    print ''
    unittest.main(verbosity=2)
