.. currentmodule:: cfdm
.. default-role:: obj
 
.. _Releases:

**Releases**
============
----

Documentation for all versions of cfdm.

.. contents::
   :local:
   :backlinks: entry

**CF-1.10**
-----------

* `Version 1.10.1.0 <https://ncas-cms.github.io/cfdm/1.10.1.0>`_ (2023-04-26)
* `Version 1.10.0.3 <https://ncas-cms.github.io/cfdm/1.10.0.3>`_ (2023-03-10)
* `Version 1.10.0.2 <https://ncas-cms.github.io/cfdm/1.10.0.2>`_ (2023-01-26)
* `Version 1.10.0.1 <https://ncas-cms.github.io/cfdm/1.10.0.1>`_ (2022-10-31)
* `Version 1.10.0.0 <https://ncas-cms.github.io/cfdm/1.10.0.0>`_ (2022-08-17)

----

**CF-1.9**
----------

* `Version 1.9.0.4 <https://ncas-cms.github.io/cfdm/1.9.0.4>`_ (2022-07-18)
* `Version 1.9.0.3 <https://ncas-cms.github.io/cfdm/1.9.0.3>`_ (2022-03-10)
* `Version 1.9.0.2 <https://ncas-cms.github.io/cfdm/1.9.0.2>`_ (2022-01-31)
* `Version 1.9.0.1 <https://ncas-cms.github.io/cfdm/1.9.0.1>`_ (2021-10-12)
* `Version 1.9.0.0 <https://ncas-cms.github.io/cfdm/1.9.0.0>`_ (2021-09-21)

----

**CF-1.8**
----------

* `Version 1.8.9.0 <https://ncas-cms.github.io/cfdm/1.8.9.0>`_ (2021-05-25)
* `Version 1.8.8.0 <https://ncas-cms.github.io/cfdm/1.8.8.0>`_ (2020-12-18)
* `Version 1.8.7.0 <https://ncas-cms.github.io/cfdm/1.8.7.0>`_ (2020-10-09)
* `Version 1.8.6.0 <https://ncas-cms.github.io/cfdm/1.8.6.0>`_ (2020-07-24)
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

Finding versions
^^^^^^^^^^^^^^^^

The version of the CF conventions and the CF data model being used may
be found with the `cfdm.CF` function:

.. code-block:: python
   :caption: *Retrieve the version of the CF conventions.*
	     
   >>> import cfdm
   >>> cfdm.CF()
   '1.10'

This indicates which version of the CF conventions are represented by
this release of the cfdm package, and therefore the version can not be
changed.

The version identifier of the cfdm package is based on the version of
the CF conventions to which it applies, with the addition of extra
integer values for updates that apply to the same version of CF:

.. code-block:: python
   :caption: *Retrieve the version of the cfdm package.*
	     	     
   >>> cfdm.__version__
   '1.10.0.0'

The next section outlines the scheme used to set version identifiers.

Versioning strategy
^^^^^^^^^^^^^^^^^^^

A ``CF.major.minor`` numeric version scheme is used, where ``CF`` is
the version of the CF conventions (e.g. ``1.10``) to which a particular
version of cfdm applies.

**Major** changes comprise:

* changes to the API, such as:

  * changing the name of an existing function or method;
  * changing the behaviour of an existing function or method;
  * changing the name of an existing keyword parameter;
  * changing the default value of an existing keyword parameter;
  * changing the meaning of a value of an existing keyword parameter.
  * introducing a new function or method;
  * introducing a new keyword parameter;
  * introducing a new permitted value of a keyword parameter;

* changes to required versions of the dependencies.

**Minor** changes comprise:

* bug fixes that do not change the API;
* changes to the documentation;
* code tidying.
