CFDM
====

----------------------------------------------------------------------

Requirements
============

* read CF-netCDF datasets into field constructs

* create new field constructs that do not exist in CF-netCDf datasets

* modify field constructs' metadata and data

* create subspaces of field constructs

* write field constructs to CF-netCDF datasets

* allow field constructs and CF-netCDF datasets to be checked for
  CF-compliance by third party libraries.

----------------------------------------------------------------------

Documentation
=============


----------------------------------------------------------------------

Dependencies
============

* **Required:** A [**python**](http://www.python.org) version 2.7.
 
* **Required:** The [**python numpy
  package**](https://pypi.python.org/pypi/numpy) at version 1.13 or
  newer.

* **Required:** The [**python netCDF4
  package**](https://pypi.python.org/pypi/netCDF4) at version 1.3.1 or
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

Command line utilities
======================

The ``cfdump`` tool generates text representations on standard output
of the CF fields contained in the input files. 

During the installation described above, these scripts will be copied
automatically to a location given by the ``PATH`` environment
variable.

For usage instructions, use the ``-h`` option to display the manual
pages:

    cfdump -h

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
