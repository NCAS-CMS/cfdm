.. currentmodule:: cfdm
.. default-role:: obj
 
.. _Releases:

**Releases**
============
----

.. contents::
   :local:
   :backlinks: entry

**CF-1.8**
----------

* `Version 1.8.6 <https://ncas-cms.github.io/cfdm/1.8.6>`_ (2020-07-??)
* `Version 1.8.5 <https://ncas-cms.github.io/cfdm/1.8.5>`_ (2020-06-10)
* `Version 1.8.4 <https://ncas-cms.github.io/cfdm/1.8.4>`_ (2020-06-08)
* `Version 1.8.3 <https://ncas-cms.github.io/cfdm/1.8.3>`_ (2020-04-30)
* `Version 1.8.2 <https://ncas-cms.github.io/cfdm/1.8.2>`_ (2020-04-24)
* `Version 1.8.1 <https://ncas-cms.github.io/cfdm/1.8.1>`_ (2020-04-14)
* `Version 1.8.0 <https://ncas-cms.github.io/cfdm/1.8.0>`_ (2020-03-23)

----

**CF-1.7**
----------

* `Version 1.7.11 <https://ncas-cms.github.io/cfdm/1.7.11>`_ (2019-11-27)
* `Version 1.7.10 <https://ncas-cms.github.io/cfdm/1.7.10>`_ (2019-11-14)
* `Version 1.7.9 <https://ncas-cms.github.io/cfdm/1.7.9>`_ (2019-11-07)
* `Version 1.7.8 <https://ncas-cms.github.io/cfdm/1.7.8>`_ (2019-10-04)
* `Version 1.7.7 <https://ncas-cms.github.io/cfdm/1.7.7>`_ (2019-06-13)
* `Version 1.7.6 <https://ncas-cms.github.io/cfdm/1.7.6>`_ (2019-06-05)
* `Version 1.7.5 <https://ncas-cms.github.io/cfdm/1.7.5>`_ (2019-05-15)
* `Version 1.7.4 <https://ncas-cms.github.io/cfdm/1.7.4>`_ (2019-05-14)
* `Version 1.7.3 <https://ncas-cms.github.io/cfdm/1.7.3>`_ (2019-04-24)
* `Version 1.7.2 <https://ncas-cms.github.io/cfdm/1.7.2>`_ (2019-04-05)
* `Version 1.7.1 <https://ncas-cms.github.io/cfdm/1.7.1>`_ (2019-04-02)
* `Version 1.7.0 <https://ncas-cms.github.io/cfdm/1.7.0>`_ (2019-04-02)

----

.. _Versioning:

**Versioning**
--------------

The version of the CF conventions and the CF data model being used may
be found with the `cfdm.CF` function:

.. code-block:: python
   :caption: *Retrieve the version of the CF conventions.*
	     
   >>> import cfdm
   >>> cfdm.CF()
   '1.8'

This indicates which version of the CF conventions are represented by
this release of the cfdm package, and therefore the version can not be
changed.

The version identifier of the cfdm package is based on the version of
the CF conventions to which it applies, with the addition of an extra
integer value that is incremented each time the package is
updated. For example, the first release for version 1.7 of the CF
conventions (CF-1.7) had cfdm version ``1.7.0``, and subsequent
releases to the package had versions ``1.7.1``, ``1.7.2``, etc. This
carried on until the first release to apply to version CF-1.8, which
was cfdm version ``1.8.0``.

.. code-block:: python
   :caption: *Retrieve the version of the cfdm package.*
	     	     
   >>> cfdm.__version__
   '1.8.2'
