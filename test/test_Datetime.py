import datetime
import os
import time 
import unittest

import numpy

import cfdm

class DatetimeTest(unittest.TestCase):
    def test_Datetime(self):  
        d = cfdm.Datetime(2003)
        d = cfdm.Datetime(2003, 2)
        d = cfdm.Datetime(2003, 2, 30)
        d = cfdm.Datetime(2003, 2, 30, 0, 0)
        d = cfdm.Datetime(2003, 2, 30, 0, 0, 0)
        d = cfdm.Datetime(2003, 4, 5, 12, 30, 15)
        d = cfdm.Datetime(year=2003, month=4, day=5, hour=12, minute=30, second=15)
#        self.assertTrue((d.year, d.month, d.day, d.hour, d.minute, d.second) == 
#                        (2003, 4, 5, 12, 30, 15))
#        self.assertTrue(d.timetuple() == (2003, 4, 5, 12, 30, 15, -1, 1, -1))
#        self.assertTrue( d == d)
#        self.assertFalse(d >  d)
#        self.assertTrue( d >= d)
#        self.assertFalse(d <  d)
#        self.assertTrue( d <= d)
#        self.assertFalse(d != d)
#        e = cfdm.Datetime(2003, 4, 5, 12, 30, 16)
#        self.assertFalse(d == e)
#        self.assertFalse(d >  e)
#        self.assertFalse(d >= e)
#        self.assertTrue( d <  e)
#        self.assertTrue( d <= e)
#        self.assertTrue( d != e)
#        e = cfdm.Datetime(2003, 4, 5, 12, 30, 14)
#        self.assertFalse(d == e)
#        self.assertTrue( d >  e)
#        self.assertTrue( d >= e)
#        self.assertFalse(d <  e)
#        self.assertFalse(d <= e)
#        self.assertTrue( d != e)
#
#        d = cfdm.Datetime(year=2003, month=4, day=5, hour=12, minute=30, second=15,
#                        microsecond=12)
#        self.assertTrue( d == d)
#        self.assertFalse(d >  d)
#        self.assertTrue( d >= d)
#        self.assertFalse(d <  d)
#        self.assertTrue( d <= d)
#        self.assertFalse(d != d)
#        e = cfdm.Datetime(year=2003, month=4, day=5, hour=12, minute=30, second=15,
#                        microsecond=11)
#        self.assertFalse(e == d)
#        self.assertFalse(e >  d)
#        self.assertFalse(e >= d)
#        self.assertTrue( e <  d)
#        self.assertTrue( e <= d)
#        self.assertTrue( e != d)
#        e = cfdm.Datetime(year=2003, month=4, day=5, hour=12, minute=30, second=15,
#                        microsecond=13)
#        self.assertFalse(e == d)
#        self.assertTrue( e >  d)
#        self.assertTrue( e >= d)
#        self.assertFalse(e <  d)
#        self.assertFalse(e <= d)
#        self.assertTrue( e != d)
#    #--- End: def        

#    def test_Datetime_utcnow(self):  
#        d = cfdm.Datetime.utcnow()
#    #--- End: def

    def test_Datetime_copy(self):  
        d = datetime.datetime.utcnow()
        e = cfdm.dt(d)
        self.assertTrue(e.equals(e.copy()))
    #--- End: def

    def test_Datetime_equals(self):  
        d = datetime.datetime.utcnow()
        e = cfdm.dt(d)
        self.assertTrue(e.equals(e))
        self.assertTrue(e.equals(d))
    #--- End: def

    def test_Datetime_replace(self):  
        d = cfdm.Datetime(1999, 4, 5, 12, 30, 15, 987654, calendar='360_day')
        e = d.replace(1787)
        self.assertTrue(e.equals(cfdm.Datetime(1787, 4, 5, 12, 30, 15, 987654, calendar='360_day')))
        e = d.replace(1787, 12, 3, 6, 23, 45, 2345, 'noleap')
        self.assertTrue(e.equals(cfdm.Datetime(1787, 12, 3, 6, 23, 45, 2345, calendar='noleap')))
    #--- End: def

    def test_Datetime_rt2dt(self): 
        self.assertTrue(
            cfdm.cfdatetime.rt2dt(1, cfdm.Units('days since 2004-2-28')) == 
            numpy.array(datetime.datetime(2004, 2, 29)))
        self.assertTrue(
            (cfdm.cfdatetime.rt2dt([1, 3], cfdm.Units('days since 2004-2-28')) == 
             numpy.array([datetime.datetime(2004, 2, 29), datetime.datetime(2004, 3, 2)])).all())
        self.assertTrue(
            (cfdm.cfdatetime.rt2dt([1, 3], cfdm.Units('days since 2004-2-28', '360_day')) == 
             numpy.array([cfdm.Datetime(2004, 2, 29), cfdm.Datetime(2004, 3, 1)])).all())
    #--- End: def

    def test_Datetime_dt2rt(self):     
        units = cfdm.Units('days since 2004-2-28')
        self.assertTrue(
            cfdm.cfdatetime.dt2rt(datetime.datetime(2004, 2, 29), None, units) ==
            numpy.array(1.0))
        self.assertTrue(
            (cfdm.cfdatetime.dt2rt([datetime.datetime(2004, 2, 29), datetime.datetime(2004, 3, 2)], None, units) ==
             numpy.array([1., 3.])).all())
        units = cfdm.Units('days since 2004-2-28', '360_day')
        self.assertTrue((cfdm.cfdatetime.dt2rt([cfdm.Datetime(2004, 2, 29), cfdm.Datetime(2004, 3, 1)], None, units) == numpy.array([1., 3.])).all())
        units = cfdm.Units('seconds since 2004-2-28')
        self.assertTrue(
            cfdm.cfdatetime.dt2rt(datetime.datetime(2004, 2, 29), None, units) == 
            numpy.array(86400.0)) 
    #--- End: def

#--- End: class


if __name__ == '__main__':
    print 'Run date:', datetime.datetime.utcnow()
    cfdm.environment()
    print
    unittest.main(verbosity=2)
