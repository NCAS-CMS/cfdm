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

.. _Python-versions:

**Python versions**
-------------------

cfdm works for Python 2.7 and Python 3.

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

.. _Source:

**Source**
----------

To install from source:

1. Download the cfdm package from https://pypi.org/project/cfdm

2. Unpack the library (replacing ``<version>`` with the version that
   you want to install, e.g. ``1.8.0``):

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

* `Python <https://www.python.org/>`_, version 2.7 or 3 or newer,

* `numpy <http://www.numpy.org/>`_, version 1.15 or newer,

* `netCDF4 <http://unidata.github.io/netcdf4-python/>`_, version 1.5.3
  or newer,

* `cftime <https://unidata.github.io/cftime/>`_, version 1.1.1 or
  newer (note that this library is istalled with netCDF4, but possibly
  not a new enough version), and

* `future <https://python-future.org/>`_, version 0.16.0 or newer.

----

.. _Code-repository:

**Code repository**
-------------------

The complete source code is available at https://github.com/NCAS-CMS/cfdm

.. .. rubric:: Footnotes

   .. [#installfiles] The ``requirements.txt`` file contains

     .. include:: ../../requirements.txt
        :literal:
     
