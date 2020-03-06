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
   '1.8.12'
