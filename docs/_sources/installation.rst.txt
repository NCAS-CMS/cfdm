.. currentmodule:: cfdm
.. default-role:: obj

.. _installation:

**Installation**
================

----

**Dependencies**
----------------

----

The cfdm package requires:

* `Python <https://www.python.org/>`_, version 2.7 or 3 or newer,

* `numpy <http://www.numpy.org/>`_, version 1.11 or newer,

* `netCDF4 <http://unidata.github.io/netcdf4-python/>`_, version 1.4.0
  or newer, and

* `future <https://python-future.org/>`_, version 0.16.0 or newer.

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

**conda**
---------

----

*Coming soon*

.. To install cfdm using `conda <https://conda.io/docs/>`_, first install
   `Anaconda <https://www.anaconda.com/download>`_ for Python 2 or Python
   3, then on type on the command line:
   
   .. code:: bash
   
      conda install -c ncas cfdm


**Source**
----------

----

To install from source:

1. Download the cfdm package from https://pypi.org/project/cfdm

2. Unpack the library:

   .. code:: bash
	 
      tar zxvf cfdm-1.7b6.tar.gz
      cd cfdm-1.7b6

3. Install the package:
  
  * To install the cfdm package to a central location:

    .. code:: bash
	 
       python setup.py install

  * To install the cfdm package locally to the user in a default
    location:

    .. code:: bash

       python setup.py install --user

  * To install the cfdm package in the <directory> of your choice:

    .. code:: bash

       python setup.py install --home=<directory>

**Tests**
---------

----

Tests are run from within the ``cfdm/test`` directory:

.. code:: bash
 
   python run_tests.py
       
**Code repository**
-------------------

----

The complete source code is available at https://github.com/NCAS-CMS/cfdm
