cfdm
====

A Python reference implementation of the CF data model at CF-1.11.

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/NCAS-CMS/cfdm?color=000000&label=latest%20version)](https://ncas-cms.github.io/cfdm/Changelog.html)
[![PyPI](https://img.shields.io/pypi/v/cfdm?color=000000)](https://pypi.org/project/cfdm/)
[![Conda](https://img.shields.io/conda/v/conda-forge/cfdm?color=000000)](https://anaconda.org/conda-forge/cfdm)

[![Conda](https://img.shields.io/conda/pn/conda-forge/cfdm?color=2d8659)](https://ncas-cms.github.io/cfdm/installation.html#operating-systems)
[![Website](https://img.shields.io/website?color=2d8659&down_message=online&label=documentation&up_message=online&url=https%3A%2F%2Fncas-cms.github.io%2Fcfdm%2F)](https://ncas-cms.github.io/cfdm/index.html)
[![GitHub](https://img.shields.io/github/license/NCAS-CMS/cfdm?color=2d8659)](https://github.com/NCAS-CMS/cfdm/blob/main/LICENSE)

[![Codecov](https://img.shields.io/codecov/c/github/NCAS-CMS/cfdm?color=006666)](https://codecov.io/gh/NCAS-CMS/cfdm)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/NCAS-CMS/cfdm/run-test-suite.yml?branch=main?color=006666&label=test%20suite%20workflow)](https://github.com/NCAS-CMS/cfdm/actions)

[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)

#### References

[![Website](https://img.shields.io/website?down_color=264d73&down_message=10.21105%2Fjoss.02717&label=JOSS&up_color=264d73&up_message=10.21105%2Fjoss.02717&url=https:%2F%2Fjoss.theoj.org%2Fpapers%2F10.21105%2Fjoss.02717%2Fstatus.svg)](https://doi.org/10.21105/joss.02717)
[![Website](https://img.shields.io/website?color=264d73&down_message=10.5281%2Fzenodo.3894524&label=DOI&up_message=10.5281%2Fzenodo.3894524&url=https%3A%2F%2Fzenodo.org%2Frecord%2F3894524%23.Xuf2uXVKjeQ)](https://doi.org/10.5281/zenodo.3894524)
[![Website](https://img.shields.io/website?down_color=264d73&down_message=10.5194%2Fgmd-10-4619-2017&label=GMD&up_color=264d73&up_message=10.5194%2Fgmd-10-4619-2017&url=https%3A%2F%2Fwww.geosci-model-dev.net%2F10%2F4619%2F2017%2F)](https://www.geosci-model-dev.net/10/4619/2017/)

Documentation
=============

https://ncas-cms.github.io/cfdm

Installation
============

https://ncas-cms.github.io/cfdm/installation

Tutorial
========

https://ncas-cms.github.io/cfdm/tutorial

Functionality
=============

The ``cfdm`` package fully implements the [CF data
model](https://cfconventions.org/cf-conventions/cf-conventions.html#appendix-CF-data-model)
for its internal data structures and so is able to process any
CF-compliant dataset. It is not strict about CF-compliance, however,
so that partially conformant datasets may be ingested from existing
datasets and written to new datasets. This is so that datasets which
are partially conformant may nonetheless be modified in memory.

The central elements defined by the CF data model are the **field
construct**, which corresponds to CF-netCDF data variable with all of
its metadata; and the **domain contruct**, which may be the domain of
a field construct or corresponds to a CF-netCDF domain variable with
all of its metadata.

A simple example of reading a field construct from a file and
inspecting it:

    >>> import cfdm
    >>> f = cfdm.read('file.nc')
    >>> f
    [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>]
    >>> print(f[0])
    Field: air_temperature (ncvar%tas)
    ----------------------------------
    Data            : air_temperature(time(12), latitude(64), longitude(128)) K
    Cell methods    : time(12): mean (interval: 1.0 month)
    Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                    : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                    : longitude(128) = [0.0, ..., 357.1875] degrees_east
                    : height(1) = [2.0] m

The ``cfdm`` package can:

* read field and domain constructs from netCDF and CDL datasets,
* create new field and domain constructs in memory,
* write and append field and domain constructs to netCDF datasets on disk,
* read, write, and manipulate UGRID mesh topologies
* read, write, and create coordinates defined by geometry cells,
* read and write netCDF4 string data-type variables,
* read, write, and create netCDF and CDL datasets containing
  hierarchical groups,
* inspect field and domain constructs,
* test whether two constructs are the same,
* modify field and domain construct metadata and data,
* create subspaces of field and domain constructs, from indices or
  metadata values,
* incorporate, and create, metadata stored in external files, and
* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays, or coordinate arrays compressed by
  subsampling), whilst presenting a view of the data in its
  uncompressed form.

Command line utility
====================

During installation the `cfdump` command line tool is also installed,
which generates text descriptions of the field constructs contained in
a netCDF dataset:

    $ cfdump file.nc
    Field: air_temperature (ncvar%tas)
    ----------------------------------
    Data            : air_temperature(time(12), latitude(64), longitude(128)) K
    Cell methods    : time(12): mean (interval: 1.0 month)
    Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                    : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                    : longitude(128) = [0.0, ..., 357.1875] degrees_east
                    : height(1) = [2.0] m

Tests
=====

Tests are run from within the ``cfdm/test`` directory:

    $ python run_tests.py

Citation
========

If you use cfdm, either as a stand-alone application or to provide a CF
data model implementation to another software library, please consider
including the reference:

Hassell et al., (2020). cfdm: A Python reference implementation of the
CF data model. Journal of Open Source Software, 5(54), 2717,
https://doi.org/10.21105/joss.02717

```
@article{Hassell2020,
  doi = {10.21105/joss.02717},
  url = {https://doi.org/10.21105/joss.02717},
  year = {2020},
  publisher = {The Open Journal},
  volume = {5},
  number = {54},
  pages = {2717},
  author = {David Hassell and Sadie L. Bartholomew},
  title = {cfdm: A Python reference implementation of the CF data model},
  journal = {Journal of Open Source Software}
}
```
