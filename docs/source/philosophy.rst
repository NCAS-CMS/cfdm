.. currentmodule:: cfdm
.. default-role:: obj

.. em dash, trimming surrounding whitespace
.. |---| unicode:: U+2014  
   :trim:
      
.. _philosophy:

**Philosophy**
==============

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

**Two levels of implementation**
--------------------------------
	       
The basic requirement of the reference implementation is to represent
the logical :ref:`CF data model <CF-data-model>` in memory with a
package of Python classes, with no further features. However, in order
to be useful the implementation must also have the practical
functionality to read and write netCDF datasets, and inspect :ref:`CF
data model constructs <CF-data-model>`.

In order to satisfy both needs there is a stand-alone core
implementation, the :ref:`cfdm.core <class_core>` package, that
includes no functionality beyond that mandated by the CF data model
(and therefore excludes any information about the netCDF encoding of
constructs). The core implementation provides the basis (via
inheritance) for the :ref:`cfdm <class_extended>` package that allows,
in addition, the reading and writing of netCDF datasets, as well as
comprehensive inspection capabilities and extra field and domain
construct modification capabilities.

----

.. _CF-conventions:

**CF conventions**
------------------

The CF data model does not enforce the CF conventions. CF-compliance
is the responsibility of the user. For example, a "units" property
whose value is not a valid `UDUNITS
<https://www.unidata.ucar.edu/software/udunits>`_ string is not
CF-compliant, but is allowed by the CF data model. This is also true,
in general, for the cfdm package. The few exceptions to this occur
when field and domain constructs are read from, or written to, a
netCDF file: it may not be possible to parse a non-CF-compliant netCDF
variable or attribute to create an unambiguous CF data model
construct; or create an unambiguous netCDF variable or attribute from
a non-CF-compliant CF data model construct.

----

**Functionality**
-----------------

The cfdm package has, with few exceptions, only the functionality
required to read and write datasets, and to create, modify and inspect
field and domain constructs in memory.

The cfdm package is not, and is not meant to be, a general analysis
package. Therefore it can't, for example, regrid field constructs to
new domains, perform statistical collapses, combine field constructs
arithmetically, etc. It has, however, been designed to be
:ref:`extensible <Extensions>` to facilitate the creation of other
packages that build on this cfdm implementation whilst also adding
extra, higher level functionality.

The `cf-python <https://ncas-cms.github.io/cf-python>`_ and `cf-plot
<http://ajheaps.github.io/cf-plot/>`_ packages, that are built on top
of the cfdm package, include much more higher level functionality.

----

**API**
-------

The design of an application programming interface (API) needs to
strike a balance between being verbose and terse. A verbose API is
easier to understand and is more memorable, but usually involves more
typing; whilst a terse API is more efficient for the experienced
user. The cfdm package has aimed for an API that is more at the
verbose end of the spectrum: in general it does not use abbreviations
for method and parameter names, and each method performs a sole
function.
