.. currentmodule:: cfdm
.. default-role:: obj

.. _installation:

Installation
============

Dependencies
------------

The `cfdm` package requires:

* **Python** version 2.7 or 3 or newer,

* **numpy** version 1.11 or newer,

* **netCDF4** version 1.4.0 or newer, and 

* **future** version 0.16.0 or newer.

conda
-----

To install `cfdm` using `conda <https://conda.io/docs/>`_, first
install `Anaconda <https://www.anaconda.com/download>`_ for Python 2
or Python 3, then on type on the command line:

.. code:: bash

   conda install -c ncas cfdm

pip
---

To install `cfdm` using `pip <https://pypi.org/project/pip/>`_, type
on the command line:

.. code:: bash

   pip install cfdm


Source
------

To install from source:

1. Download the `cfdm` package from https://pypi.org/project/cfdm

2. Unpack the library:

   .. code:: bash
	 
      tar zxvf cfdm-1.7.tar.gz
      cd cfdm-1.7

3. Install the package:
  
  * To install the `cfdm` package to a central location:

    .. code:: bash
	 
       python setup.py install

  * To install the `cfdm` package locally to the user in a default location:

    .. code:: bash

       python setup.py install --user

  * To install the `cfdm` package in the <directory> of your choice:

    .. code:: bash

       python setup.py install --home=<directory>

Code repository
---------------

The complete source code is available at https://github.com/NCAS-CMS/cfdm
