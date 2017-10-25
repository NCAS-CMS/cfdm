import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class FieldTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        self.f = cfdm.read(self.filename)

        self.test_only = []

    def test_FieldList___add_____iadd__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)

        f = f + f.copy()
        self.assertTrue(len(f) == 2)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f += (f[0].copy(),)
        self.assertTrue(len(f) == 3)

        f += [f[0].copy()]
        self.assertTrue(len(f) == 4)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f += list(f[0].copy())
        self.assertTrue(len(f) == 5)

        f += f.copy()
        self.assertTrue(len(f) == 10)

        f = f + f.copy()
        self.assertTrue(len(f) == 20)
    #--- End: def

    def test_FieldList___contains__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        f.append(f[0].copy())
        f[1].data[...] = f[1].array * 10
        
        g = cfdm.read(self.filename)[0]
        self.assertTrue(g in f)
    #--- End: def

    def test_FieldList___len__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        
        self.assertTrue(len(cfdm.FieldList()) == 0)
        self.assertTrue(len(f) == 1)
        f.append(f[0].copy())
        self.assertTrue(len(f) == 2)
        f.extend(f.copy())
        self.assertTrue(len(f) == 4)
    #--- End: def

    def test_FieldList___mul_____imul__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.FieldList()
        f = f * 4
        self.assertTrue(len(f) == 0)
        self.assertTrue(isinstance(f, cfdm.FieldList))
        
        f = cfdm.FieldList()
        f *= 4
        self.assertTrue(len(f) == 0)
        self.assertTrue(isinstance(f, cfdm.FieldList))
        
        f = cfdm.read(self.filename)
        f = f * 4
        self.assertTrue(len(f) == 4)
        self.assertTrue(isinstance(f, cfdm.FieldList))
        
        f = cfdm.read(self.filename)
        f *= 4
        self.assertTrue(len(f) == 4)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f = f * 2
        self.assertTrue(len(f) == 8)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f *= 3
        self.assertTrue(len(f) == 24)
        self.assertTrue(isinstance(f, cfdm.FieldList))
    #--- End: def

    def test_FieldList___repr__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        f += f

        s = '''[<Field: eastward_wind(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) m s-1>,
 <Field: eastward_wind(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) m s-1>]'''

        self.assertTrue(repr(f) == s)
    #--- End: def

    def test_FieldList_append(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.FieldList()

        f.append(cfdm.read(self.filename)[0])
        self.assertTrue(len(f) == 1)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f.append(f[0].copy())
        self.assertTrue(len(f) == 2)
        self.assertTrue(isinstance(f, cfdm.FieldList))
                
        f.append(f[0].copy())
        self.assertTrue(len(f) == 3)
    #--- End: def

    def test_FieldList_copy(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        f.append(f[0].copy())
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
    #--- End: def

    def test_FieldList_count(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)

        self.assertTrue(f.count(f[0]) == 1)

        f *= 7
        self.assertTrue(f.count(f[0]) == 7)

        f[3] = f[0].copy()
        f[3].data[...] = f[3].array * 99

        f[5] = f[0].copy()
        f[5].data[...] = f[0].array * 99
                
        self.assertTrue(f.count(f[0]) == 5)
        self.assertTrue(f.count(f[3]) == 2)
    #--- End: def

    def test_FieldList_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
        
        f += g.copy()
        self.assertTrue(len(f) == 2)
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
    #--- End: def

    def test_FieldList_extend(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.FieldList()

        f.extend(cfdm.read(self.filename))
        self.assertTrue(len(f) == 1)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f.extend(f.copy())
        self.assertTrue(len(f) == 2)
        self.assertTrue(isinstance(f, cfdm.FieldList))
                
        f.extend(f.copy())
        self.assertTrue(len(f) == 4)
    #--- End: def

    def test_FieldList_insert(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f[0].copy()
                
        f.insert(0, g.copy())
        self.assertTrue(len(f) == 2)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        g = g.copy()
        g.data[...] = g.array + 10
        
        f.insert(-1, g)
        self.assertTrue(len(f) == 3)
        self.assertTrue((f[0].array == (f[1].array - 10)).all())
        self.assertTrue(isinstance(f, cfdm.FieldList))
    #--- End: def

    def test_FieldList_remove(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f[0].copy()
                
        f.append(g)
        self.assertTrue(len(f) == 2)
        
        f.remove(g)
        self.assertTrue(len(f) == 1)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        f.remove(f[0].copy())
        self.assertTrue(len(f) == 0)
        self.assertTrue(isinstance(f, cfdm.FieldList))
    #--- End: def

    def test_FieldList_pop(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f[0]
        h = g.copy()
        f.append(h)

        z = f.pop(0)
        self.assertTrue(z is g)
        self.assertTrue(len(f) == 1)
        self.assertTrue(isinstance(f, cfdm.FieldList))

        z = f.pop(-1)
        self.assertTrue(z is h)
        self.assertTrue(len(f) == 0)
        self.assertTrue(isinstance(f, cfdm.FieldList))
    #--- End: def

    def test_FieldList_reverse(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f[0]
        h = g.copy()
        f.append(h)

        self.assertTrue(g is f[0])
        self.assertTrue(h is f[1])

        f.reverse()
        self.assertTrue(isinstance(f, cfdm.FieldList))
        self.assertTrue(len(f) == 2)
        self.assertTrue(g is f[1])
        self.assertTrue(h is f[0])
    #--- End: def

    def test_FieldList_select(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)

        g = f.select('not this one')
        self.assertTrue(isinstance(g, cfdm.FieldList))
        self.assertTrue(len(g) == 0)

        g = f.select('eastw')
        self.assertTrue(isinstance(g, cfdm.FieldList))
        self.assertTrue(len(g) == 1)

        f *= 9
        f[4] = f[0].copy()
        f[4].standard_name = 'this one'
        f[6] = f[0].copy()
        f[6].standard_name = 'this one'

        g = f.select('eastw')
        self.assertTrue(isinstance(g, cfdm.FieldList))
        self.assertTrue(len(g) == 7)

        g = f.select('this one')
        self.assertTrue(isinstance(g, cfdm.FieldList))
        self.assertTrue(len(g) == 2)
    #--- End: def

    def test_FieldList_set_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.filename)
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
        
        f += g.copy()
        self.assertTrue(len(f) == 2)
        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))
    #--- End: def

#--- End: class

if __name__ == '__main__':
    print 'Run date:', datetime.datetime.now()
    cfdm.environment()
    print''
    unittest.main(verbosity=2)
