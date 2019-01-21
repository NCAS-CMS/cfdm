.. currentmodule:: cfdm
.. default-role:: obj

.. _Installation:

**Installation**
================

----

Version |release| for version |version| of the CF conventions.

.. _Dependencies:

**Dependencies**
----------------

----

The cfdm package requires:

* `Python <https://www.python.org/>`_, version 2.7 or 3 or newer,

* `numpy <http://www.numpy.org/>`_, version 1.11 or newer,

* `cftime <https://unidata.github.io/cftime/>`_, version 1.0 or
  newer,

* `netCDF4 <http://unidata.github.io/netcdf4-python/>`_, version 1.4.0
  or newer, and

* `future <https://python-future.org/>`_, version 0.16.0 or newer.

.. _pip:
  
**pip**
-------

----

To install cfdm and all of its dependencies run, for example:

.. code-block:: shell
   :caption: *Install as root, with any missing dependencies.*
	     
   pip install cfdm

.. code-block:: shell
   :caption: *Install as a user, with any missing dependencies.*
	     
   pip install cfdm --user

To install cfdm without any of its dependencies then run, for example:

.. code-block:: shell
   :caption: *Install as root without installing any of the
             dependencies.*
	     
   pip install cfdm --no-deps

See the `documentation for pip install
<https://pip.pypa.io/en/stable/reference/pip_install/>`_ for further
options.

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
	 
      tar zxvf cfdm-1.7.0b12.tar.gz
      cd cfdm-1.7.0b12

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

During installation the ``cfdump`` command line tool is also
installed, which generates text descriptions of the field constructs
contained in a netCDF dataset.

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

.. .. rubric:: Footnotes

   .. [#installfiles] The ``requirements.txt`` file contains

     .. include:: ../../requirements.txt
        :literal:
     
