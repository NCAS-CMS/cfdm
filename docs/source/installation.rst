.. currentmodule:: cfdm
.. default-role:: obj

.. _Installation:

**Installation**
================

Version |release| for version |version| of the CF conventions.

----

.. _Dependencies:

**Dependencies**
----------------

----

The cfdm package requires:

* `Python <https://www.python.org/>`_, version 2.7 or 3 or newer,

* `numpy <http://www.numpy.org/>`_, version 1.11 or newer,

* `netCDF4 <http://unidata.github.io/netcdf4-python/>`_, version 1.4.0
  or newer, and

* `future <https://python-future.org/>`_, version 0.16.0 or newer.

.. _pip:
  
**pip**
-------

----

`pip install <https://pip.pypa.io/en/latest/reference/pip_install/>`_
can be used, for example:

.. code:: bash

   pip install cfdm

.. code:: bash

   pip install cfdm --user

.. code:: bash

   pip install cfdm --target <dir>

.. _conda:

**conda**
---------

----

*Coming soon*

.. To install cfdm using `conda <https://conda.io/docs/>`_, first install
   `Anaconda <https://www.anaconda.com/download>`_ for Python 2 or Python
   3, then on type on the command line:
   
   .. code:: bash
   
      conda install -c ncas cfdm

.. _Source:

**Source**
----------

----

To install from source:

1. Download the cfdm package from https://pypi.org/project/cfdm

2. Unpack the library:

   .. code:: bash
	 
      tar zxvf cfdm-1.7b7.tar.gz
      cd cfdm-1.7b7

3. Install the package:
  
  * To install the cfdm package to a central location:

    .. code:: bash
	 
       python setup.py install

  * To install the cfdm package locally to the user in the default
    location:

    .. code:: bash

       python setup.py install --user

  * To install the cfdm package in the <directory> of your choice:

    .. code:: bash

       python setup.py install --home=<directory>

.. _Command-line-utility:

**Command line utility**
------------------------

----

During installation the `!cfdump` command line tool is also installed,
which generates text descriptions of the field constructs contained in
a netCDF dataset.

.. _Tests:

**Tests**
---------

----

Tests are run from within the ``cfdm/test`` directory:

.. code:: bash
 
   python run_tests.py
       
.. _Code-repository:

**Code repository**
-------------------

----

The complete source code is available at https://github.com/NCAS-CMS/cfdm
