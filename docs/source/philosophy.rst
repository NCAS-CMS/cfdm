.. currentmodule:: cfdm
.. default-role:: obj

.. _philosophy:

	     
Philosophy
==========

The basic requirement of a reference implementation is to represent
the logical CF data model in memory with a package of Python classes,
and no further features. However, to be useful, the implementation
must also have the practical functionality to read and write
real-world netCDF datasets.

In order to satisfy both needs there is a stand-alone core
implementation, the :ref:`cfdm.core <class_core>` package, that
includes no functionality beyond that mandated by the CF data
model. This core implementation provides the basis for an extended
implementation, the :ref:`cfdm <class_extended>` package, that allows
the reading and writing of netCDF datasets, as well as having a more
user-friendly API.

.. code:: python

   >>> import numpy
   >>> import cfdm
   >>> f = cfdm.core.Field(properties={'standard_name': 'altitude'})
   >>> axis = f.set_construct('domain_axis', cfdm.core.DomainAxis(1))
   >>> f.set_data(cfdm.core.NumpyArray(numpy.array([115.])), axes=[axis]) TODO AttributeError: 'Field' object has no attribute 'domain_axes'

   >>> print(f)
   constructs, properties TODO -> get rid of __repr__?

.. code:: python

   >>> import cfdm
   >>> f = cfdm.Field(properties={'standard_name': 'altitude'})
   >>> axis = f.set_domain_axis(cfdm.DomainAxis(1))
   >>> f.set_data(cfdm.Data([115.]), axes=[axis])
   >>> prin(f)
   Field: altitude
   ---------------
   Data            : altitude(cfdm%domainaxis0(1)) TODO (cfdm%)
   Dimension coords:    TODO
