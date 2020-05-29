from __future__ import print_function
import datetime
import os
import tempfile
import unittest

import numpy
import netCDF4

import cfdm


class DSGTest(unittest.TestCase):
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
        # cfdm.LOG_LEVEL('DISABLE')

        self.contiguous = 'DSG_timeSeries_contiguous.nc'
        self.indexed = 'DSG_timeSeries_indexed.nc'
        self.indexed_contiguous = 'DSG_timeSeriesProfile_indexed_contiguous.nc'

        (fd, self.tempfilename) = tempfile.mkstemp(
            suffix='.nc', prefix='cfdm_', dir='.')
        os.close(fd)

        a = numpy.ma.masked_all((4, 9), dtype=float)
        a[0, 0:3] = [0.0, 1.0, 2.0]
        a[1, 0:7] = [1.0, 11.0, 21.0, 31.0, 41.0, 51.0, 61.0]
        a[2, 0:5] = [2.0, 102.0, 202.0, 302.0, 402.0]
        a[3, 0:9] = [3.0, 1003.0, 2003.0, 3003.0, 4003.0,
                     5003.0, 6003.0, 7003.0, 8003.0]
        self.a = a

        b = numpy.array([[[20.7, -99, -99, -99],
                          [10.1, 11.8, 18.2, -99],
                          [11.0, 11.8, -99, -99],
                          [16.3, 20.0, -99, -99],
                          [13.8, 18.3, -99, -99],
                          [15.9 , -99, -99, -99],
                          [15.7, 21.2, -99, -99],
                          [22.5, -99, -99, -99],
                          [18.0, -99, -99, -99],
                          [12.6, 21.7, -99, -99],
                          [10.5, 12.9, 21.0, -99],
                          [16.0, 19.7, -99, -99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99]],

                         [[5.2, 5.8, 10.8, 13.8],
                          [2.6, 9.2, -99, -99],
                          [0.7, 4.0, -99, -99],
                          [15.7, -99, -99, -99],
                          [2.5, 16.0, -99, -99],
                          [4.6, 9.8, -99, -99],
                          [0.6, 3.1, -99, -99],
                          [3.8, -99, -99, -99],
                          [5.7, 12.9, 18.1, -99],
                          [3.9, 6.9, 16.9, -99],
                          [7.3, 13.8, 16.0, -99],
                          [4.5, 9.8, 11.3, -99],
                          [1.5, -99, -99, -99],
                          [0.9, 4.3, 6.2, -99],
                          [1.7, 9.9, -99, -99],
                          [9.3, -99, -99, -99],
                          [0.7, -99, -99, -99],
                          [15.7, -99, -99, -99],
                          [0.7, 1.2, -99, -99],
                          [4.5, 12.4, 13.0, -99],
                          [3.5, 6.8, 7.9, -99],
                          [8.1, 12.2, -99, -99],
                          [5.9, -99, -99, -99],
                          [1.0, 9.6, -99, -99],
                          [5.6, 7.8, 9.1, -99],
                          [7.1, 9.0, 10.4, -99]],

                         [[35.2, -99, -99, -99],
                          [34.7, 38.9, 48.1, -99],
                          [35.2, 39.3, 39.6, -99],
                          [40.3, 40.4, 48.0, -99],
                          [30.0, 36.5, -99, -99],
                          [33.3, 43.3, -99, -99],
                          [37.7, -99, -99, -99],
                          [33.5, -99, -99, -99],
                          [31.9, 33.7, -99, -99],
                          [34.1, 35.4, 41.0, -99],
                          [30.2, 33.7, 38.7, -99],
                          [32.4, 42.4, -99, -99],
                          [33.2, 34.9, 39.7, -99],
                          [33.2, -99, -99, -99],
                          [38.5, -99, -99, -99],
                          [37.3, 39.9, -99, -99],
                          [30.0, 39.1, -99, -99],
                          [36.4, 39.1, 45.6, -99],
                          [41.0, -99, -99, -99],
                          [31.1, -99, -99, -99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99],
                          [-99,-99,-99,-99]]])

        b = numpy.ma.where(b==-99, numpy.ma.masked, b)
        self.b = b

        self.test_only = []

    def tearDown(self):
        os.remove(self.tempfilename)

    def test_DSG_contiguous(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.contiguous)

        self.assertEqual(len(f), 2)

        # Select the specific humidity field
        q = [g for g in f
             if g.get_property('standard_name') == 'specific_humidity'][0]

        self.assertTrue(q._equals(self.a, q.data.array))

        cfdm.write(f, self.tempfilename)
        g = cfdm.read(self.tempfilename)

        self.assertEqual(len(g), len(f))

        for i in range(len(f)):
            self.assertTrue(g[i].equals(f[i], verbose=3))

        # ------------------------------------------------------------
        # Test creation
        # ------------------------------------------------------------
        # Define the ragged array values
        ragged_array = numpy.array([280, 282.5, 281, 279, 278, 279.5],
                                   dtype='float32')

        # Define the count array values
        count_array = [2, 4]

        # Create the count variable
        count_variable = cfdm.Count(data=cfdm.Data(count_array))
        count_variable.set_property('long_name',
                                    'number of obs for this timeseries')

        # Create the contiguous ragged array object
        array = cfdm.RaggedContiguousArray(
                         compressed_array=cfdm.NumpyArray(ragged_array),
                         shape=(2, 4), size=8, ndim=2,
                         count_variable=count_variable)

        # Create the field construct with the domain axes and the ragged
        # array
        tas = cfdm.Field()
        tas.set_properties({'standard_name': 'air_temperature',
                            'units': 'K',
                            'featureType': 'timeSeries'})

        # Create the domain axis constructs for the uncompressed array
        X = tas.set_construct(cfdm.DomainAxis(4))
        Y = tas.set_construct(cfdm.DomainAxis(2))

        # Set the data for the field
        tas.set_data(cfdm.Data(array), axes=[Y, X])

        cfdm.write(tas, self.tempfilename)

    def test_DSG_indexed(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.indexed)

        self.assertEqual(len(f), 2)

        # Select the specific humidity field
        q = [g for g in f
             if g.get_property('standard_name') == 'specific_humidity'][0]

        self.assertTrue(q._equals(q.data.array, self.a))

        cfdm.write(f, self.tempfilename)
        g = cfdm.read(self.tempfilename)

        self.assertEqual(len(g), len(f))

        for i in range(len(f)):
            self.assertTrue(g[i].equals(f[i], verbose=3))

    def test_DSG_indexed_contiguous(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = cfdm.read(self.indexed_contiguous)

        self.assertEqual(len(f), 2)

        # Select the specific humidity field
        q = [g for g in f
             if g.get_property('standard_name') == 'specific_humidity'][0]

        qa = q.data.array

        message= repr(qa-self.b) +'\n'+repr(qa[2,0])+'\n'+repr(self.b[2, 0])
        self.assertTrue(q._equals(qa, self.b), message)

        cfdm.write(f, self.tempfilename)
        g = cfdm.read(self.tempfilename)

        self.assertEqual(len(g), len(f))

        for i in range(len(f)):
            self.assertTrue(g[i].equals(f[i], verbose=3))

    def test_DSG_create_contiguous(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Define the ragged array values
        ragged_array = numpy.array([1, 3, 4, 3, 6], dtype='float32')
        # Define the count array values
        count_array = [2, 3]

        # Initialise the count variable
        count_variable = cfdm.Count(data=cfdm.Data(count_array))
        count_variable.set_property('long_name',
                                    'number of obs for this timeseries')

        # Initialise the contiguous ragged array object
        array = cfdm.RaggedContiguousArray(
            compressed_array=cfdm.Data(ragged_array),
            shape=(2, 3), size=6, ndim=2,
            count_variable=count_variable)

        # Initialize the auxiliary coordinate construct with the
        # ragged array and set some properties
        z = cfdm.AuxiliaryCoordinate(
            data=cfdm.Data(array),
            properties={'standard_name': 'height',
                        'units': 'km',
                        'positive': 'up'})

        self.assertTrue((z.data.array == numpy.ma.masked_array(
            data=[[1.0, 3.0, 99],
                  [4.0, 3.0, 6.0]],
            mask=[[False, False,  True],
                  [False, False, False]],
            fill_value=1e+20,
            dtype='float32')).all())

        self.assertEqual(z.data.get_compression_type(), 'ragged contiguous')

        self.assertTrue((z.data.compressed_array == numpy.array(
            [1., 3., 4., 3., 6.], dtype='float32')).all())

        self.assertTrue((z.data.get_count().data.array == numpy.array(
            [2, 3])).all())


#--- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.utcnow())
    cfdm.environment(display=False)
    print()
    unittest.main(verbosity=2)

