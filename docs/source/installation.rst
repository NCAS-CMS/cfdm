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

cfdm works for Python versions 3.7 or newer.

----

.. _pip:
  
**pip**
-------

To install cfdm and all of its :ref:`dependencies <Dependencies>` run,
for example:

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

----

.. _conda:

**conda**
---------

The cfdm package is in the :ref:`conda-forge
<https://anaconda.org/conda-forge/cfdm>` conda channel. To install
cfdm with all of its :ref:`dependencies <Dependencies>` run

.. code-block:: console
   :caption: *Install with conda.*

   $ conda install -c conda-forge cfdm

----

.. _Source:

**Source**
----------

To install from source:

1. Download the cfdm package from https://pypi.org/project/cfdm

2. Unpack the library (replacing ``<version>`` with the version that
   you want to install, e.g. ``1.10.0.0``):

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

The cfdm package requires:

* `Python <https://www.python.org/>`_, version 3.7 or newer.

* `numpy <http://www.numpy.org/>`_, version 1.15 or newer.

* `netCDF4 <https://pypi.org/project/netCDF4/>`_, version 1.5.4 or
  newer.

* `cftime <https://pypi.org/project/cftime/>`_, version 1.6.0 or
  newer.

* `netcdf_flattener <https://pypi.org/project/netcdf-flattener/>`_,
  version 1.2.0 or newer.

* `packaging <https://pypi.org/project/packaging/>`_, version 20.0 or
  newer.

----

.. _Code-repository:

**Code repository**
-------------------

The source code is available at https://github.com/NCAS-CMS/cfdm

.. .. rubric:: Footnotes

   .. [#installfiles] The ``requirements.txt`` file contains

     .. include:: ../../requirements.txt
        :literal:
     
