CFDM
====

A reference implementation of the [**CF data
model**](https://www.geosci-model-dev.net/10/4619/2017/)

----------------------------------------------------------------------

Functionality
=============

* read netCDF datasets into field constructs

* create new field constructs in memory

* inspect field constructs

* modify field construct metadata and data in memory

* create subspaces of field constructs

* write field constructs to a CF-netCDF dataset on disk

----------------------------------------------------------------------

Documentation
=============


----------------------------------------------------------------------

Dependencies
============

* **Required:** [**python**](http://www.python.org) version 2.7, 3 or
    later.
 
* **Required:** The [**python numpy
  package**](https://pypi.python.org/pypi/numpy) at version 1.13 or
  newer.

* **Required:** The [**python netCDF4
  package**](https://pypi.python.org/pypi/netCDF4) at version 1.4 or
  newer. This package requires the
  [**netCDF**](http://www.unidata.ucar.edu/software/netcdf),
  [**HDF5**](http://www.hdfgroup.org/HDF5) and
  [**zlib**](ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4)
  libraries.

----------------------------------------------------------------------

Tests
=====

The test scripts are in the ``test`` directory. To run all tests:

    python test/run_tests.py


----------------------------------------------------------------------

Code license
============

[**MIT License**](http://opensource.org/licenses/mit-license.php)

  * Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use, copy,
    modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

  * The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

  * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
