Post processing
===============

This is simply a very basic introduction to some of the more widely used useful tools for viewing, checking, and converting UM input and output data. The tools described below all run on the ARCHER login nodes, and you can run them there, but they also run on the ARCHER post-processors (see http://www.archer.ac.uk/documentation/user-guide/connecting.php#sec-2.1.2). Try logging on to one of the post-processors for these exercises: ``ssh -X espp1`` (fieldop must currently be run onteh ARCHER login node). The post processors can see /home and /work and /nerc.

xconv
-----

**i. View data**

On ARCHER go to the output directory of the global job that you ran previously (the one copied from xleha). Run ``xconv`` on the file ending with ``da19810902_00``. This file is an atmosphere start file - this type of file is used to restart the model from the time specified in the file header data.

Run a second instance of ``xconv`` on the file whose name ends in ``.astart``. This is the file used by the model to start its run - created by the reconfiguration program in this case.

The ``xconv`` window lists the fields in the file, the dimensions of those fields (upper left panel), the coordinates of the grid underlying the data, the time(s) of the data (upper right panel), some information about the type of file (lower left panel), and general data about the field (lower right panel.)

Both files have the same fields. Double click on a field to reveal its coordinate data. Check the time for this field (select the "t" checkbox in the upper right panel).

Plot both sets of data - click the "Plot Data" button.

View the data - this shows numerical data values and their coordinates and can be helpful for finding spurious data values.

**ii. Convert UM fields data to netCDF**

Select a single-level field (one for which nz=1), choose "Output format" to be "Netcdf", enter an "Output file name", and select "Convert". Information relevant to the file conversion will appear in the lower left panel.

Use ``xconv`` to view the netcdf file just created.

uminfo
------

You can view the header information for the fields in a UM file by using the utility ``uminfo`` - redirect the output to a file or pipe it to ``less``: :: 

  archer$ uminfo <one-of-your-fields-files> | less

The output from this command is best viewed in conjunction with the Unified Model Documentation Paper F3 which explains in depth the various header fields.

pumf
----

Run ``pumf`` on the start file - here's an example on one of grenvill's files: :: 

 archer$ pumf xjpgza_da006
 PUMF successful
 Header output in: /work/n02/n02/ncastr01/tmp/tmp.eslogin005.16599/
                   pumf_head.ncastr01.d14076.t150856.28259
 Field output in:  /work/n02/n02/ncastr01/tmp/tmp.eslogin005.16599/
                   pumf_field.ncastr01.d14076.t150856.28259


This provides another way of seeing header information, but also gives some information about the fields themselves. The output from pumf is a pair of text files. Use your favourite editor to view the output.

cumf
----

You can compare two UM fields files with ``cumf``.  Note, differences in header information can arise even when field data is identical. Try running ``cumf`` on the two start files referred to above (in the View data section) - try running ``cumf`` on a file and itself.

fieldop
-------

Note - please ensure you are on the ARCHER login node for this exercise.

``fieldop`` allows you to add, subtract, multiply, divide files field value by field value. Particularly useful is the subtract option: :: 

 archer$ export SCRATCH=/work/n02/n02/ncastr<your id>
 archer$ fieldop -s xjpgya_ca009 xjpgya_ca010 output
 FIELDOP output in: /work/n02/n02/ncastr01/fieldop.out.29843

Note fieldop creates 2 files; the file in this case called ``output`` which is itself a fields file (in this case the difference of xjpgya_ca009 and xjpgya_ca010) and a file explaining how fieldop has run (a bit like a .leave file).
Run this on your two start files. Use ``xconv`` to view the difference file. This is a useful tool to help you find where a model may be "blowing up".

ff2pp
-----

We have mentioned on the presentations the PP file format - this is a sequential format (a fields file is random access) still much used in the community. PP data is stored as 32-bit, which provides a significant saving of space, but means that a conversion step is required from a fields file (64-bit). The utility to do this is ff2pp (some confusion has arisen in the past with a similar utility written by the MO - be sure to use the CMS version located in /work/n02/n02/hum/bin - you can check that you are using the right one by typing ``which ff2pp``. Try using it on some of your fields files - here's an example ::
 
 archer$ cd /work/n02/n02/grenvill/um/xklka
 archer$ ff2pp xklkaa.pa1981sep xklkaa.pa1981sep.pp

 file xklkaa.pa1981sep is a byte swapped 64 bit ieee um file
 archer$ ls -l xklkaa.pa1981sep*
 -rw-r--r-- 1 grenvill n02 46559232 Nov 26 10:37 xklkaa.pa1981sep
 -rw-r--r-- 1 grenvill n02 19567200 Nov 28 10:45 xklkaa.pa1981sep.pp

Note the reduction in file size - ff2pp does a lossy compression of data, but 32-bits is probably enough for diagnostics. Now use xconv to examine the contents of the PP file.

cfa and cfdump
--------------

There is an increasing use of python in the community and we have, and
continue to develop, python tools to do much of the data processing
previously done using IDL or MATLAB and are working to extend that
functionality. ``cfa`` is a python utility which offers a host of
features - we'll use it to convert UM fields file or PP data to
CF-compliant data in NetCDF format. You first need to set the
environment to run ``cfa`` - if you will be a frequent user, add the
``module load`` and ``module swap`` commands to your .profile. ::

 esPP001$ module load anaconda cf
 esPP001$ module swap PrgEnv-cray PrgEnv-intel
 esPP001$ cfa -i -o xklkaa.pa1981sep.pp.nc xklkaa.pa1981sep.pp
 
Try viewing the NetCDF file with xconv.


``cfdump`` is a tool to view CF fields. It can be run on PP or NetCDF
files, to provide a text representation of the CF fields contained in
the input files. Try it on a PP file and its NetCDF equivalent,
e.g. ::

 esPP001$ cfdump xklkaa.pa1981sep.pp | more
 surface_temperature field summary
 ---------------------------------
 Data           : surface_temperature(latitude(145), longitude(192)) K
 Cell methods   : time: mean
 Axes           : time(1) = [1981-09-01 12:00:00] 360_day
                : latitude(145) = [-90.0, ..., 90.0] degrees_north
                : longitude(192) = [0.0, ..., 358.125] degrees_east

 PP_1_26001_vn802 field summary
 ------------------------------
 Data           : PP_1_26001_vn802(latitude(180), longitude(360)) 
 Cell methods   : time: mean
 Axes           : time(1) = [1981-09-01 13:10:00] 360_day
                : latitude(180) = [-89.5, ..., 89.5] degrees_north
                : longitude(360) = [0.5, ..., 359.5] degrees_east
  
 
CF-python CF-plot
-----------------

Many tools exist for analsing data from NWP and climate models and there are many contributing factors for the proliferation of these analysis utilities, for example, the disparity of data formats used by the authors of the models, and/or the availability of the underlying sofware. There is a strong push towards developing and using python as the underlying language and CF-netCDF as the data format. CMS is home to tools in the CF-netCDF stable - here's an example of the use of these tools to perform some quite complex data manipulations. The user is insulated from virtually all of the details of the methods allowing them to concentrate on scientific analysis rather than programming intricacies.





* Set up the environment and start python - if you will be a frequent
  user, add the ``module load`` and ``module swap`` commands to your
  .profile. ::

   archer$ module load anaconda cf
   archer$ module swap PrgEnv-cray PrgEnv-intel
   archer$ python
   >>> import cf

We'll be looking at CRU observed precipitation data

* Read in data files ::

  >>> f = cf.read('/home/n02/n02/charles/UM_Training_2015/cru/*.nc')

* Inspect the file contents with different amounts of detail ::

  >>> f
  >>> print f
  >>> f.dump()
  
Note that the three files in the cru directory are aggregated into one
field.

* Average the field with respect to time ::

  >>> f = f.collapse('T: mean')
  >>> print f

Note that the time coordinate is now of length 1.

* Read in another field produced by a GCM, this has a different latitude/longitude grid to regrid the CRU data to ::

  >>> g = cf.read('/home/n02/n02/charles/UM_Training_2015/N96_DJF_precip_means.nc')
  >>> print g

* Regrid the field of observed data (f) to the grid of the model field (g) ::

  >>> f = f.regrids(g)
  >>> print f

* Subspace the regridded field, f, to a European region ::

  >>> f = f.subspace(X=cf.wi(-10, 40), Y=cf.wi(35, 70))
  >>> print f

Note that the latitude and longitude coordinates are now shorter in length.

* Import the cfplot visualisation library ::

  >>> import cfplot

* Make a default contour plot of the field, f ::

   >>> cfplot.con(f)


* Write out the new field f to disk ::

  >>> cf.write(f, 'cru_precis_european_mean_regridded.nc')
