.. currentmodule:: cfdm
.. default-role:: obj

.. _subclassing:

**Subclassing**
===============

----

Version |release| for version |version| of the CF conventions.


Creating a new implementation of the CF data model by subclassing cfdm
classes is straight forward. For example:

.. code-block:: python
   :caption: *Create a new implementation with a new field construct
             class.*

   import cfdm
   
   class my_Field(cfdm.Field):
       def info(self):
           return 'I am a {!r} instance'.format(self.__class__.__name__)

   f = my_Field()
   f.set_property('standard_name', 'air_pressure')
   
   
It is also possible use `cfdm.read` and `cfdm.write` to read and write
respectively field constructs defined by the new implementation; and
`cfdm.example_field` to return example field constructs defined by the
new implementation. For example:

.. code-block:: python
   :caption: *Encapsulate the new implementation in a
             CFDMImplementation class instance and define new read and
             write functions that pass the new implementation to the the
             appropriate cfdm function.*	     

   import functools

   # Define an implementation that is the same as cfdm, but which uses
   # the my_Field class to represent field constructs
   my_implementation = cfdm.implementation()
   my_implementation.set_class('Field', my_Field)

   # Define a new function that reads a dataset and returns field
   # constructs in my_Field instances   
   my_read = functools.partial(cfdm.read,
                               _implementation=my_implementation)

   # Define a new function that writes my_Field instances to disk   
   my_write = functools.partial(cfdm.write,
                                _implementation=my_implementation)

   # Read the dataset file.nc, as used in the tutorial
   q, t = my_read('file.nc')

   # Write the new field constructs to disk
   my_write([q, t], 'new_file.nc')


.. code-block:: python
   :caption: *Inspect a field construct read from the dataset,
              demonstrating that it is a my_Field instance from the
              new implementation that has the inherited functionality
              of a cfdm.Field instance.*

   >>> print(type(t))
   <class '__main__.my_Field'>  
   >>> print(t.info())
   I am a 'my_Field' instance
   >>> print(t)
   Field: air_temperature (ncvar%ta)
   ---------------------------------
   Data            : air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K
   Cell methods    : grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees) time(1): maximum
   Field ancils    : air_temperature standard_error(grid_latitude(10), grid_longitude(9)) = [[0.76, ..., 0.32]] K
   Dimension coords: atmosphere_hybrid_height_coordinate(1) = [1.5]
                   : grid_latitude(10) = [2.2, ..., -1.76] degrees
                   : grid_longitude(9) = [-4.7, ..., -1.18] degrees
                   : time(1) = [2019-01-01 00:00:00]
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m     
   >>> print(t.data.array)
   [[[262.8 270.5 279.8 269.5 260.9 265.0 263.5 278.9 269.2]
     [272.7 268.4 279.5 278.9 263.8 263.3 274.2 265.7 279.5]
     [269.7 279.1 273.4 274.2 279.6 270.2 280.0 272.5 263.7]
     [261.7 260.6 270.8 260.3 265.6 279.4 276.9 267.6 260.6]
     [264.2 275.9 262.5 264.9 264.7 270.2 270.4 268.6 275.3]
     [263.9 263.8 272.1 263.7 272.2 264.2 260.0 263.5 270.2]
     [273.8 273.1 268.5 272.3 264.3 278.7 270.6 273.0 270.6]
     [267.9 273.5 279.8 260.3 261.2 275.3 271.2 260.8 268.9]
     [270.9 278.7 273.2 261.7 271.6 265.8 273.0 278.5 266.4]
     [276.4 264.2 276.3 266.1 276.1 268.1 277.0 273.4 269.7]]]


Modification and extension of the implementation functionality used by
`cfdm.read` and `cfdm.write` is possible by subclassing the
`CFDMImplementation`, `NetCDFRead` and `NetCDFWrite` classes. See
`cf-python <https://github.com/NCAS-CMS/cf-python>` for an example of
this customisation.
