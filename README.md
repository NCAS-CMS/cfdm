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

Installation
============

* To install version 1.2.1 by [**conda**](http://conda.pydata.org/docs):

        conda install -c ncas -c scitools cf-python cf-plot  
        conda install -c nesii esmpy

    These two commands will install cf-python, all of its required
    dependencies and the two optional packages cf-plot (for
    visualisation) and ESMF (for regridding). To install cf-python and
    all of its required dependencies alone:

        conda install -c ncas -c scitools cf-python 

    To update cf-python, cf-plot and ESMF to the latest versions::

        conda update -c ncas -c scitools cf-python cf-plot 
        conda update -c nesii esmpy

* To install the **latest** version from
  [**PyPI**](https://pypi.python.org/pypi/cf-python):

        pip install cf-python

* To install from source:

    1. Download the cf package from [**cf-python
       downloads**](https://bitbucket.org/cfpython/cf-python/downloads).
    
    2. Unpack the library:
    
            tar zxvf cf-python-1.3.2.tar.gz
            cd cf-python-1.3.2
  
    3. Install the package:
            
      * To install the cf package to a central location:
         
              python setup.py install
         
      * To install the cf package locally to the user in a default
        location:
  
              python setup.py install --user
        
      * To install the cf package in the ``<directory>`` of your
        choice:
        
              python setup.py install --home=<directory>

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

The ``cfa`` tool creates and writes to disk the CF fields contained in
the input files.

During the installation described above, these scripts will be copied
automatically to a location given by the ``PATH`` environment
variable.

For usage instructions, use the ``-h`` option to display the manual
pages:

    cfdump -h
    cfa -h

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
