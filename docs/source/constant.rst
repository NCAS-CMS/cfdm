.. currentmodule:: cfdm
.. default-role:: obj
		  
**cfdm constants**
==================

----

Version |release| for version |version| of the CF conventions.

**Data**
--------

.. data:: cfdm.masked

    A constant that allows data values to be masked by direct
    assignment. This is consistent with the :ref:`behaviour of numpy
    masked arrays <numpy:maskedarray.generic.constructing>`.

    For example, masking every element of a field construct's data
    array could be done as follows:

    >>> f[...] = cfdm.masked
    
