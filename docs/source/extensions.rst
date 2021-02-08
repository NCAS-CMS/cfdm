.. currentmodule:: cfdm
.. default-role:: obj

.. _Extensions:

**Extensions**
==============

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

The cfdm package has been designed to be subclassed, so that the
creation of a new implementation of the CF data model, based on cfdm,
is straight forward. For example:

.. code-block:: python
   :caption: *Create a new implementation with a new field construct
             class.*

   import cfdm
   
   class my_Field(cfdm.Field):
       def info(self):
           return 'I am a {!r} instance'.format(
               self.__class__.__name__)
   
The interpretation of CF-netCDF files that is encoded within the
`cfdm.read` and `cfdm.write` functions is also inheritable, so that an
extended data model implementation need *not* recreate the complicated
mapping of CF data model constructs to, and from, CF-netCDF
elements. This is made possible by the `bridge design pattern
<https://en.wikipedia.org/wiki/Bridge_pattern>`_, that decouples the
implementation of the CF data model from the CF-netCDF encoding so
that the two can vary independently.

.. code-block:: python
   :caption: *Define an implementation that is the same as cfdm, but
              which uses the my_Field class to represent field
              constructs*   
	      
   >>> my_implementation = cfdm.implementation()
   >>> my_implementation.set_class('Field', my_Field)

.. code-block:: python
   :caption: *Define new functions that can read into my_Field
              instances, and write write my_Field instances to
              datasets on disk.*
   
   >>> import functools
   >>> my_read = functools.partial(cfdm.read,
   ...                             _implementation=my_implementation)
   >>> my_write = functools.partial(cfdm.write,
   ...                              _implementation=my_implementation)

.. code-block:: python
   :caption: *Read my_field constructs from 'file.nc', the netCDF file
              used in the tutorial, using the new my_read
              function. Inspect a field construct read from the
              dataset, demonstrating that it is a my_Field instance
              from the new implementation that has the inherited
              functionality of a cfdm.Field instance.*

   >>> q, t = my_read('file.nc')
   >>> print(type(q))
   <class '__main__.my_Field'>  
   >>> print(q.info())
   I am a 'my_Field' instance
   >>> print(repr(q))
   <my_Field: specific_humidity(latitude(5), longitude(8)) 1>
   >>> print(q.data.array)
   [[0.007 0.034 0.003 0.014 0.018 0.037 0.024 0.029]
    [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
    [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
    [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
    [0.006 0.036 0.019 0.035 0.018 0.037 0.034 0.013]]

.. code-block:: python
   :caption: *Write the my_field constructs to a netCDF file using the
             new my_write function.*
	     
   >>> my_write([q, t], 'new_file.nc')

Note that, so far, we have only replaced the field construct class in
the new implementation, and not any of the metadata constructs or
other component classes:
    
.. code-block:: python
   :caption: *Demonstrate that the metadata construct classes of
             within the my_Field instance are still cfdm classes.*

   >>> print(type(q))
   <class '__main__.my_Field'>  
   >>> print(type(q.construct('latitude')))
   <class 'cfdm.dimensioncoordinate.DimensionCoordinate'>

If the API of the new implementation is changed such that a given cfdm
functionality has a different API in the new implementation, then the
new read-from-disk and write-to-disk functions defined above can still
be used provided that the new implementation is created from a
subclass of `cfdm.CFDMImplementation`, with the new API being applied
in overridden methods.

.. code-block:: python
   :caption: *Create an implementation with a different API.*
   
   class my_Field_2(cfdm.Field):
      def my_coordinates(self):
          """Get coordinate constructs with a different API."""
          c = self.coordinates
          if not c:
              return {}
          return c
   
   class my_CFDMImplementation(cfdm.CFDMImplementation):
      def get_coordinates(self, field):
          """Get coordinate constructs from a my_Field_2 instance,
          using its different API.
          """
          return field.my_coordinates()
   
   my_implementation_2 = my_CFDMImplementation(
      cf_version=cfdm.CF(),
      
      Field=my_Field_2,
      
      AuxiliaryCoordinate=cfdm.AuxiliaryCoordinate,
      CellMeasure=cfdm.CellMeasure,
      CellMethod=cfdm.CellMethod,
      CoordinateReference=cfdm.CoordinateReference,
      DimensionCoordinate=cfdm.DimensionCoordinate,
      DomainAncillary=cfdm.DomainAncillary,
      DomainAxis=cfdm.DomainAxis,
      FieldAncillary=cfdm.FieldAncillary,
      
      Bounds=cfdm.Bounds,
      InteriorRing=cfdm.InteriorRing,
      CoordinateConversion=cfdm.CoordinateConversion,
      Datum=cfdm.Datum,
      
      List=cfdm.List,
      Index=cfdm.Index,
      Count=cfdm.Count,
      NodeCountProperties=cfdm.NodeCountProperties,
      PartNodeCountProperties=cfdm.PartNodeCountProperties,
      
      Data=cfdm.Data,
      GatheredArray=cfdm.GatheredArray,
      NetCDFArray=cfdm.NetCDFArray,
      RaggedContiguousArray=cfdm.RaggedContiguousArray,
      RaggedIndexedArray=cfdm.RaggedIndexedArray,
      RaggedIndexedContiguousArray=cfdm.RaggedIndexedContiguousArray,
   )

As all classes are required for the initialisation of the new
implementation class, this demonstrates explicitly that, in the absence
of subclasses of the other classes, the cfdm classes may be used.

.. code-block:: python
   :caption: *Read the file into 'my_Field_2' instances.*
	 
   >>> my_read_2 = functools.partial(cfdm.read,
   ...                               _implementation=my_implementation2)
   >>> q, t = my_read_2('file.nc')
   >>> print(repr(q))
   <my_Field_2: specific_humidity(latitude(5), longitude(8)) 1>

Finally, the mapping of CF data model constructs from CF-netCDF
elements, and vice versa, may be modified where desired, leaving all
other aspects it unchanged

.. code-block:: python
   :caption: *Modify the mapping of netCDF elements to CF data model
              instances.*
	 
   class my_NetCDFRead(cfdm.read_write.netcdf.NetCDFRead):
       def read(self, filename):
           """Read my fields from a netCDF file on disk or from
           an OPeNDAP server location, using my modified mapping
           from netCDF to the CF data model.
           """
           print("Reading dataset using my modified mapping")
           return super().read(filename)

.. code-block:: python
   :caption: *Create a new read-from-disk function that uses the
              modified mapping.*
	     
   my_netcdf = my_NetCDFRead(my_implementation_2)
   def my_read_3(filename, ):
       """Read my field constructs from a dataset."""
       return my_netcdf.read(filename)
   
.. code-block:: python
   :caption: *Read the file from disk into 'my_Field_2' instances,
              demonstrating that the modified mapping is being used.*
	   
   >>> q, t = my_read_3('~/cfdm/docs/source/sample_files/file.nc')
   Reading dataset using my modified mapping
   >>> print(repr(q))
   <my_Field_2: specific_humidity(latitude(5), longitude(8)) 1>

In the same manner, `cfdm.read_write.netcdf.NetCDFWrite` may be
subclassed, and a new write-to-disk function defined, to override
aspects of the mapping from CF data model constructs to netCDF
elements in a dataset.

The _custom dictionary
^^^^^^^^^^^^^^^^^^^^^^

All cfdm classes have a `_custom` attribute that contains a dictionary
meant for use in external subclasses.

It is intended for the storage of extra objects that are required by
an external subclass, yet can be transfered to copied instances using
the inherited cfdm infrastructure. The `_custom` dictionary is shallow
copied, rather than deep copied, when using the standard cfdm deep
copy method techniques (i.e. the `!copy` method, initialisation with
the *source* parameter, or applying the `copy.deepcopy` function) so
that subclasses of cfdm are not committed to potentially expensive
deep copies of the dictionary values, of which cfdm has no
knowledge. Note that calling `copy.deepcopy` on a cfdm (sub)class
simply invokes its `!copy` method. The cfdm library itself does not
use the `_custom` dictionary, other than to pass on a shallow copy of
it to copied instances.

The consequence of this shallow-copy behaviour is that if an external
subclass stores a mutable object within its custom dictionary then, by
default, a deep copy will contain the identical mutable object, to
which in-place changes will affect both the original and copied
instances.

To account for this, the external subclass can either simply commit to
never updating such mutables in-place (which is can be acceptable for
private quantities which are tightly controlled); or else include
extra code that does deep copy such mutables when any deep copy (or
equivalent) operation is called. The latter approach should be
implemented in the subclass's `__init__` method, similarly to this:

.. code-block:: python
   :caption: *Ensure that the _custom dictionary 'x' value is deep
             copied when a deep copy of an instance is requested.*

   import copy
   
   class my_Field_3(cfdm.Field):
       def __init__(self, properties=None, source=None, copy=True,
                    _use_data=True):
           super().__init__(properties=properties, source=source,
                            copy=copy, _use_data=_use_data)
           if source and copy:
   	       # Deep copy the custom 'x' value
               try:
    	           self._custom['x'] = copy.deepcopy(source._custom['x'])
               except (AttributeError, KeyError):
                   pass  
	   
Documentation
^^^^^^^^^^^^^

The cfdm package uses a "docstring rewriter" that allows commonly used
parts of class method docstrings to be written once in a central
location, and then inserted into each class at import time. In
addition, parts of a docstring are modified to reflect the appropriate
package and class names. This functionality extends to subclasses of
cfdm classes. New docstring substitutions may also be defined for the
subclasses.

See `cfdm.core.meta.DocstringRewriteMeta` for details on how to add to
create new docstring substitutions for extensions, and how to modify
the substitutions defined in the cfdm package.


A complete example
^^^^^^^^^^^^^^^^^^

See `cf-python <https://github.com/NCAS-CMS/cf-python>`_ for a
complete example of extending the cfdm package in the manner described
above.

cf-python adds more flexible inspection, reading and writing; and
provides metadata-aware analytical processing capabilities such as
regridding and statistical calculations.

It also has a more sophisticated data class that subclasses
`cfdm.Data`, but allows for larger-than-memory manipulations and
parallel processing.

cf-python strictly extends the cfdm API, so that a cfdm command will
always work on its cf-python counterpart.
