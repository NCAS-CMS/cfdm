.. currentmodule:: cfdm
.. default-role:: obj

.. _versioning:

**Versioning**
==============

----

Version |release| for version |version| of the CF conventions.

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
the CF conventions to which it applies, with the addition of extra
integer values for updates that apply to the same version of CF. See
https://github.com/NCAS-CMS/cfdm/blob/master/CONTRIBUTING.md for
details.

.. code-block:: python
   :caption: *Retrieve the version of the cfdm package.*
	     	     
   >>> cfdm.__version__
   '1.8.6.0'
