import datetime
import math
import os
import unittest

import cfdm

class UnitsTest(unittest.TestCase):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_file.nc')
    chunk_sizes = (17, 34, 300, 100000)[::-1]

    def test_Units___eq__(self):
        self.assertTrue(cfdm.Units('')==cfdm.Units(''))
        self.assertTrue(cfdm.Units('18')==cfdm.Units('18'))
        self.assertTrue(cfdm.Units('1')==cfdm.Units('1'))
        self.assertTrue(cfdm.Units('m')==cfdm.Units('m'))
        self.assertTrue(cfdm.Units('m')==cfdm.Units('metres'))
        self.assertTrue(cfdm.Units('m')==cfdm.Units('meTRES'))

        self.assertTrue(cfdm.Units('days since 2000-1-1')==cfdm.Units('d since 2000-1-1 0:0'))
        self.assertTrue(cfdm.Units('days since 2000-1-1')!=cfdm.Units('h since 1234-1-1 0:0'))
        
        self.assertTrue(cfdm.Units('days since 2000-1-1')==cfdm.Units('d since 2000-1-1 0:0', calendar='gregorian'))
        self.assertTrue(cfdm.Units('days since 2000-1-1')==cfdm.Units('d since 2000-1-1 0:0', calendar='standard'))
        
        self.assertTrue(cfdm.Units(calendar='noleap')==cfdm.Units(calendar='noleap'))
        self.assertTrue(cfdm.Units(calendar='noleap')==cfdm.Units(calendar='365_day'))
        self.assertTrue(cfdm.Units(calendar='nOLEAP')==cfdm.Units(calendar='365_dAY'))
        
        self.assertTrue(cfdm.Units('days since 2000-1-1', calendar='all_leap')==cfdm.Units('d since 2000-1-1 0:0', calendar='366_day'))
        self.assertTrue(cfdm.Units('days since 2000-1-1', calendar='all_leap')!=cfdm.Units('h since 2000-1-1 0:0', calendar='366_day'))    
    #--- End: def
        
    def test_Units_equivalent(self):
        self.assertTrue(cfdm.Units('').equivalent(cfdm.Units('')))
        self.assertTrue(cfdm.Units('').equivalent(cfdm.Units('1')))
        self.assertTrue(cfdm.Units('').equivalent(cfdm.Units('18')))
        self.assertTrue(cfdm.Units('18').equivalent(cfdm.Units('1')))
        self.assertTrue(cfdm.Units('18').equivalent(cfdm.Units('18')))
        self.assertTrue(cfdm.Units('1)').equivalent(cfdm.Units('1')))

        self.assertTrue(cfdm.Units('m').equivalent(cfdm.Units('m')))
        self.assertTrue(cfdm.Units('meter').equivalent(cfdm.Units('km')))
        self.assertTrue(cfdm.Units('metre').equivalent(cfdm.Units('mile')))

        self.assertTrue(cfdm.Units('s').equivalent(cfdm.Units('h')))
        self.assertTrue(cfdm.Units('s').equivalent(cfdm.Units('day')))
        self.assertTrue(cfdm.Units('second').equivalent(cfdm.Units('month')) )   

        self.assertTrue(cfdm.Units(calendar='noleap').equivalent(cfdm.Units(calendar='noleap')))
        self.assertTrue(cfdm.Units(calendar='noleap').equivalent(cfdm.Units(calendar='365_day')))
        self.assertTrue(cfdm.Units(calendar='nOLEAP').equivalent(cfdm.Units(calendar='365_dAY')))

        self.assertTrue(cfdm.Units('days since 2000-1-1').equivalent(cfdm.Units('d since 2000-1-1 0:0')))
        self.assertTrue(cfdm.Units('days since 2000-1-1').equivalent(cfdm.Units('h since 1234-1-1 0:0')))
        self.assertTrue(cfdm.Units('days since 2000-1-1').equivalent(cfdm.Units('d since 2000-1-1 0:0', calendar='gregorian')))
        self.assertTrue(cfdm.Units('days since 2000-1-1').equivalent(cfdm.Units('h since 1234-1-1 0:0', calendar='standard')))

        self.assertTrue(cfdm.Units('days since 2000-1-1', calendar='all_leap').equivalent(cfdm.Units('d since 2000-1-1 0:0', calendar='366_day')))
        self.assertTrue(cfdm.Units('days since 2000-1-1', calendar='all_leap').equivalent(cfdm.Units('h since 1234-1-1 0:0', calendar='366_day')))    
    #--- End: def 

    def test_Units_BINARY_AND_UNARY_OPERATORS(self):
        self.assertTrue((cfdm.Units('m')*2)    ==cfdm.Units('2m'))
        self.assertTrue((cfdm.Units('m')/2)    ==cfdm.Units('0.5m'))
        self.assertTrue((cfdm.Units('m')//2)   ==cfdm.Units('0.5m'))
        self.assertTrue((cfdm.Units('m')+2)    ==cfdm.Units('m @ -2'))
        self.assertTrue((cfdm.Units('m')-2)    ==cfdm.Units('m @ 2'))
        self.assertTrue((cfdm.Units('m')**2)   ==cfdm.Units('m2'))
        self.assertTrue((cfdm.Units('m')**-2)  ==cfdm.Units('m-2'))
        self.assertTrue((cfdm.Units('m2')**0.5)==cfdm.Units('m'))
    
        u = cfdm.Units('m')
        v = u
        u *= 2
        self.assertTrue(u==cfdm.Units('2m'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u /= 2
        self.assertTrue(u==cfdm.Units('0.5m'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u //= 2
        self.assertTrue(u==cfdm.Units('0.5m'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u += 2
        self.assertTrue(u==cfdm.Units('m @ -2'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u -= 2
        self.assertTrue(u==cfdm.Units('m @ 2'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u **= 2
        self.assertTrue(u==cfdm.Units('m2'))
        self.assertTrue(u!=v)
    
        self.assertTrue((2*cfdm.Units('m')) ==cfdm.Units('2m'))
        self.assertTrue((2/cfdm.Units('m')) ==cfdm.Units('2 m-1'))
        self.assertTrue((2//cfdm.Units('m'))==cfdm.Units('2 m-1'))
        self.assertTrue((2+cfdm.Units('m')) ==cfdm.Units('m @ -2'))
        self.assertTrue((2-cfdm.Units('m')) ==cfdm.Units('-1 m @ -2'))
    
        self.assertTrue((cfdm.Units('m')*cfdm.Units('2m')) ==cfdm.Units('2 m2'))
        self.assertTrue((cfdm.Units('m')/cfdm.Units('2m')) ==cfdm.Units('0.5'))
        self.assertTrue((cfdm.Units('m')//cfdm.Units('2m'))==cfdm.Units('0.5'))
    
        u = cfdm.Units('m')
        v = u
        u *= u
        self.assertTrue(u==cfdm.Units('m2'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u /= u
        self.assertTrue(u==cfdm.Units('1'))
        self.assertTrue(u!=v)
        u = cfdm.Units('m')
        v = u
        u //= u
        self.assertTrue(u==cfdm.Units('1'))
        self.assertTrue(u!=v)
    
        self.assertTrue(cfdm.Units('m').log(10)    ==cfdm.Units('lg(re 1 m)'))
        self.assertTrue(cfdm.Units('m').log(2)     ==cfdm.Units('lb(re 1 m)'))
        self.assertTrue(cfdm.Units('m').log(math.e)==cfdm.Units('ln(re 1 m)'))
        self.assertTrue(cfdm.Units('m').log(1.5)   ==cfdm.Units('2.46630346237643 ln(re 1 m)'))    
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print 'Run date:', datetime.datetime.now()
    print cfdm.environment()
    print ''
    unittest.main(verbosity=2)
