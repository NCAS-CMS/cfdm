.. currentmodule:: cfdm
.. default-role:: obj

.. _Installation:

**Installation**
================

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

.. note:: The latest version to be released and the newest versions
          available from the Python package index (PyPI) and conda are
          confirmed at `the top of the README document
          <https://github.com/NCAS-CMS/cfdm#cfdm>`_.

.. _Python-versions:

**Operating systems**
---------------------

cfdm works for Linux, Mac and Windows operating systems.

**Python versions**
-------------------

cfdm works for Python versions 3.10 or newer.

----

.. _pip:
  
**pip**
-------

To install cfdm and all of its :ref:`dependencies <Dependencies>`
(apart from :ref:`UDUNITS <UDUNITS>`) run, for example:

.. code-block:: console
   :caption: *Install as root, with any missing dependencies.*
	     
   $ pip install cfdm

.. code-block:: console
   :caption: *Install as a user, with any missing dependencies.*
	     
   $ pip install cfdm --user

To install cfdm without any of its dependencies then run, for example:

.. code-block:: console
   :caption: *Install as root without installing any of the
             dependencies.*
	     
   $ pip install cfdm --no-deps

See the `documentation for pip install
<https://pip.pypa.io/en/stable/reference/pip_install/>`_ for further
options.

.. _UDUNITS:

UDUNITS
^^^^^^^

UDUNITS (a C library that provides support for units of physical
quantities) is a required dependency that is not installed by ``pip``,
but it can be installed in a ``conda`` environment:

.. code-block:: console

   $ conda install -c conda-forge udunits2

Alternatively, UDUNITS is often available from operating system
software download managers, or may be installed from source.
    
Note that :ref:`some environment variables might also need setting
<UNIDATA-UDUNITS-2-library>` in order for the UDUNITS library to work
properly, although the defaults are usually sufficient.

----

.. _conda:

**conda**
---------

The cfdm package is in the
`conda-forge <https://anaconda.org/conda-forge/cfdm>`_  conda channel.
To install cfdm with all of its :ref:`dependencies <Dependencies>` run:

.. code-block:: console
   :caption: *Install with conda.*

   $ conda install -c conda-forge cfdm udunits2

Note that :ref:`some environment variables might also need setting
<UNIDATA-UDUNITS-2-library>` in order for the UDUNITS library to work
properly, although the defaults are usually sufficient.

----

.. _Source:

**Source**
----------

To install from source:

1. Download the cfdm package from https://pypi.org/project/cfdm

2. Unpack the library (replacing ``<version>`` with the version that
   you want to install, e.g. ``1.11.0.0``):

   .. code:: console
	 
      $ tar zxvf cfdm-<version>.tar.gz
      $ cd cfdm-<version>

3. Install the package:
  
  * To install the cfdm package to a central location:

    .. code:: console
	 
       $ python setup.py install

  * To install the cfdm package locally to the user in the default
    location:

    .. code:: console

       $ python setup.py install --user

  * To install the cfdm package in the ``<directory>`` of your choice:

    .. code:: console

       $ python setup.py install --home=<directory>

Note that :ref:`some environment variables might also need setting
<UNIDATA-UDUNITS-2-library>` in order for the UDUNITS library to work
properly, although the defaults are usually sufficient.

----

.. _cfdump-utility:

**cfdump utility**
------------------

During installation the :ref:`cfdump command line utility <cfdump>` is
also installed, which generates text descriptions of the :term:`field
constructs <field construct>` contained in a netCDF dataset.

----

.. _Tests:

**Tests**
---------

Tests are run from within the ``cfdm/test`` directory:

.. code:: console
 
   $ python run_tests.py
       
----

.. _Dependencies:

**Dependencies**
----------------

.. _Required:

Required
^^^^^^^^

The cfdm package requires:

* `Python <https://www.python.org>`_, version 3.10 or newer.

* `numpy <http://www.numpy.org>`_, version 2.0.0 or newer.

* `netCDF4 <https://pypi.org/project/netCDF4>`_, version 1.7.2 or
  newer.

* `cftime <https://pypi.org/project/cftime>`_, version 1.6.4 or
  newer.

* `h5netcdf <https://pypi.org/project/h5netcdf>`_, version 1.3.0
  newer.

* `h5py <https://pypi.org/project/h5py>`_, version 3.12.1 or newer.

* `s3fs <https://pypi.org/project/s3fs>`_, version 2024.6.0 or newer.

* `dask <https://pypi.org/project/dask>`_, version 2025.5.1 or newer.

* `distributed <https://pypi.org/project/distributed>`_, version 2025.5.1
  or newer.

* `packaging <https://pypi.org/project/packaging>`_, version 20.0 or
  newer.

* `scipy <https://scipy.org/>`_, version 1.10.0 or newer.

* `uritools <https://pypi.org/project/uritools>`_, version 4.0.3 or
  newer.

* `cfunits <https://pypi.org/project/cfunits>`_, version 3.3.7 or
  newer.

.. _UNIDATA-UDUNITS-2-library:

* `UNIDATA UDUNITS-2 library
  <http://www.unidata.ucar.edu/software/udunits>`_, version 2.2.25
  or newer. UDUNITS-2 is a C library that provides support for units of
  physical quantities.

  If the UDUNITS-2 shared library file (``libudunits2.so.0`` on
  GNU/Linux or ``libudunits2.0.dylibfile`` on MacOS) is in a
  non-standard location then its directory path should be added to the
  ``LD_LIBRARY_PATH`` environment variable.

  It may also be necessary to specify the location (directory path
  *and* file name) of the ``udunits2.xml`` file in the
  ``UDUNITS2_XML_PATH`` environment variable, although the default
  location is usually correct. For example, ``export
  UDUNITS2_XML_PATH=/home/user/anaconda3/share/udunits/udunits2.xml``.
  If you get a run-time error that looks like ``assert(0 ==
  _ut_unmap_symbol_to_unit(_ut_system, _c_char_p(b'Sv'), _UT_ASCII))``
  then setting the ``UDUNITS2_XML_PATH`` environment variable is the
  likely solution.

Optional
^^^^^^^^

Some further dependencies that enable further functionality are
optional. This is to facilitate cfdm being installed in restricted
environments for which these features are not required.

.. rubric:: Zarr

* `zarr <https://pypi.org/project/zarr>`_, version 3.1.3 or newer.

  For reading and writing Zarr datasets.

----

.. _Code-repository:

**Code repository**
-------------------

The source code is available at https://github.com/NCAS-CMS/cfdm

.. .. rubric:: Footnotes

   .. [#installfiles] The ``requirements.txt`` file contains

     .. include:: ../../requirements.txt
        :literal:
     
