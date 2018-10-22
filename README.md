cfdm
====

----------------------------------------------------------------------

A python reference implementation of the CF data model.

Description
===========

----------------------------------------------------------------------

The CF (Climate and Forecast) metadata conventions (http://cfconventions.org) provide a description of the physical
meaning of data and of their spatial and temporal properties and are designed to promote the creation, processing, and sharing of climate
and forecasting data using Network Common Data Form (netCDF, https://www.unidata.ucar.edu/software/netcdf) files and libraries.

The CF data model identifies the fundamental elements of CF and shows
how they relate to each other, independently of the netCDF encoding.

The field construct, which corresponds to a CF-netCDF data variable
with all of its metadata, is central to the CF data model. The field
construct consists of a data array and the definition of its domain,
ancillary metadata fields defined over the same domain, and cell
method constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain. The
domain itself is defined collectively by various other constructs
included in the field: domain axis, dimension coordinate, auxiliary
coordinate, cell measure, coordinate reference and domain ancillary
constructs. See https://www.geosci-model-dev.net/10/4619/2017/ for
full details.

The **cfdm** library implements the CF data model for its internal
data structures and so is able to process any CF-compliant dataset. It
is, however, not strict about CF compliance so that partially
conformant datasets may be modified in memory as well as ingested from
existing datasets, or written to new datasets.

The **cfdm** package can

* read netCDF datasets into field constructs

* create new field constructs in memory

* inspect field constructs

* modify field construct metadata and data in memory

* create subspaces of field constructs

* write field constructs to a netCDF dataset on disk

Quick start
===========

----------------------------------------------------------------------

* Make sure [**numpy**](https://pypi.python.org/pypi/numpy) (1.13 or
  newer) and [**netCDF4**](https://pypi.python.org/pypi/netCDF4) (1.4
  or newer) are installed, and you have
  [**Python**](http://www.python.org) 2.7 or newer.

Tests
=====

----------------------------------------------------------------------

The test scripts are in the ``test`` directory. To run all tests:

    python test/run_tests.py


Documentation
=============

----------------------------------------------------------------------

See the online [**documentation**](https://ncas-cms.github.io/cfdm)
for more details.

----------------------------------------------------------------------

Code license
============

----------------------------------------------------------------------

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
