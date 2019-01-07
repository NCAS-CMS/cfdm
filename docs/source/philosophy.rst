.. currentmodule:: cfdm
.. default-role:: obj

.. _philosophy:

	     
**Philosophy**
==============

----

Version |release| for version |version| of the CF conventions.

The basic requirement of the reference implementation is to represent
the logical CF data model in memory with a package of Python classes,
and no further features. However, to be useful, the implementation
must also have practical functionality to read, write, inspect, and
modify netCDF datasets.

In order to satisfy both needs there is a stand-alone core
implementation, the :ref:`cfdm.core <class_core>` package, that
includes no functionality beyond that mandated by the CF data
model. This core implementation provides the basis for an extended
implementation, the :ref:`cfdm <class_extended>` package, that allows
the reading and writing of netCDF datasets, as well as having
comprehensive inspection capabilities, and some more sophisticated
field modification methods.

**Functionality**
-----------------

----

The cfdm package has, with very few exceptions, only the functionality
required to read and write datasets, and to create and inspect field
constructs in memory.

The cfdm package is not, and is not meant to be, a general analysis
package. Therefore it can't, for example, regrid field constructs to
new domains, perform statistical collapses, combine field constructs
arithmetically, etc.

It has been designed to be :ref:`subclassable <subclassing>` so that
gemeral analyses packages define their own field constructs that have
extra functionality.

**API**
-------

----

The design of the application programming interface (API) needs to
strike a balance between being verbose and terse. A verbose API is
easier to understand, is more memorable, but usually involves more
typing; whilst a terse API is more efficient for the experienced
user. The cfdm package has aimed for an API that is more at the
verbose end of the spectrum: in general it does not use abbreviations
for method and parameter names, and each method performs a sole
function.

Here is an example of a simple field created with the :ref:`cfdm.core
<class_core>` package:

.. code:: python

   >>> import numpy
   >>> import cfdm
   >>> f = cfdm.core.Field(properties={'standard_name': 'altitude'})
   >>> axis = f.set_construct(cfdm.core.DomainAxis(1))
   >>> data = cfdm.core.Data(cfdm.core.NumpyArray(numpy.array([115.])))
   >>> f.set_data(data, axes=[axis])
   >>> print(f.get_array())
   [ 115.]
   >>> print(f)
   <cfdm.core.field.Field object at 0x7faf6ac23510>

The same field may be created with the :ref:`cfdm <class_extended>`
package:

.. code:: python

   >>> import cfdm
   >>> f = cfdm.Field(properties={'standard_name': 'altitude'})
   >>> axis = f.set_construct(cfdm.DomainAxis(1))
   >>> f.set_data(cfdm.Data([115.]), axes=[axis])
   >>> print(f.get_array())
   [ 115.]
   >>> print(f)
   Field: altitude
   ---------------
   Data            : altitude(cid%domainaxis0(1))
