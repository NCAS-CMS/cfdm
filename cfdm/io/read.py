from __future__ import print_function
from past.builtins import basestring

import os

from .. import __version__

from .. import (AuxiliaryCoordinate,
                CellMethod,
                CellMeasure,
                CoordinateReference,
                DimensionCoordinate,
                DomainAncillary,
                DomainAxis,
                Field,
                FieldAncillary,
                Bounds,
                Count,
                List,
                Index,
                CoordinateConversion,
                Datum)

from ..data import (Data,
                    GatheredArray,
                    NetCDFArray,
                    RaggedContiguousArray,
                    RaggedIndexedArray,
                    RaggedIndexedContiguousArray)

from . import CFDMImplementation

from .netcdf import NetCDFRead

implementation = CFDMImplementation(version = __version__,

                                    AuxiliaryCoordinate = AuxiliaryCoordinate,
                                    CellMeasure         = CellMeasure,
                                    CellMethod          = CellMethod,
                                    CoordinateReference = CoordinateReference,
                                    DimensionCoordinate = DimensionCoordinate,
                                    DomainAncillary     = DomainAncillary,
                                    DomainAxis          = DomainAxis,
                                    Field               = Field,
                                    FieldAncillary      = FieldAncillary,
                                    
                                    Bounds = Bounds,
                                    List   = List,
                                    Index=Index,
                                    Count=Count,
                                    
                                    CoordinateConversion = CoordinateConversion,
                                    Datum                = Datum,
                                    
                                    Data                         = Data,
                                    GatheredArray                = GatheredArray,
                                    NetCDFArray                  = NetCDFArray,
                                    RaggedContiguousArray        = RaggedContiguousArray,
                                    RaggedIndexedArray           = RaggedIndexedArray,
                                    RaggedIndexedContiguousArray = RaggedIndexedContiguousArray,
                                    )

def read(filename, external_files=(), field=None, _debug=False,
         _implementation=implementation):
    '''Read fields from a netCDF datraset.

The dataset may be on disk or on a OPeNDAP server.

.. versionadded:: 1.7

.. seealso:: `cfdm.write`

:Parameters:

    filename: `str`
        A string giving the file name or OPenDAP URL from which to
        read fields. Various type of expansion are applied to the file
        name:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial ``~`` or ``~user`` is
                                replaced by that *user*'s home
                                directory.
           
          Environment variable  Occurences of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.
          ====================  ======================================

        *Example:*
          If the environment variable ``MYSELF`` has been set to
          ``david``, then ``'~$MYSELF/data.nc'`` is equivalent to
          ``'~david/data.nc'``.
    
    external_files: (sequence of) `str`, optional

  
    field: (sequence of) `str`, optional
        Create extra, independent fields from field metadata
        constructs. The *field* parameter may be one, or a sequence,
        of:

          ==========================  ================================
          *field*                     Field components
          ==========================  ================================
          ``'field_ancillary'``       Field ancillary constructs
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ==========================  ================================

        *Example:*
          To create fields from auxiliary coordinate constructs:
          ``field='auxiliary_coordinate'`` or
          ``field=['auxiliary_coordinate']``.

        *Example:*
          To create fields from domain ancillary and cell measure
          constructs: ``field=['domain_ancillary', 'cell_measure']``.

        An extra field created via the *field* parameter will have a
        domain limited to that which can be inferred from the
        corresponding netCDF variable, without the connections that
        are defined by the parent netCDF data variable. It is possbile
        to create independent fields from metadata constructs that do
        incorporate as much of the parent field's domain as possible
        by using the `~cfdm.Field.field` method of the returned
        fields, instead of setting the *field* parameter.

:Returns:
    
    out: `list`
        A list of the fields found in the dataset. The list may be
        empty.

**Examples:**

TODO

    '''
    # Parse the field parameter
    if field is None:
        field = ()
    elif isinstance(field, basestring):
        field = (field,)

    filename = os.path.expanduser(os.path.expandvars(filename))
    
    if os.path.isdir(filename):
        raise IOError("Can't read directory {}".format(filename))

    if not os.path.isfile(filename):
        raise IOError("Can't read non-existent file {}".format(filename))

    # ----------------------------------------------------------------
    # Read the fields in the file
    # ----------------------------------------------------------------
    return  _read_a_file(filename,
                         external_files=external_files,
                         field=field,
                         _debug=_debug,
                         _implementation=_implementation)
#--- End: def

def _read_a_file(filename,
                 external_files=(),
                 field=(),
                 _debug=False,
                 _implementation=None):
    '''Read the contents of a single file into a field list.

:Parameters:

    filename: `str`
        The file name.
    
:Returns:

    out: `list`
        The fields in the file.

    '''
    # ----------------------------------------------------------------
    # Initialise a netCDF read object
    # ----------------------------------------------------------------
    netcdf = NetCDFRead(_implementation)

    # ----------------------------------------------------------------
    # Read the file into fields.
    # ----------------------------------------------------------------
    if netcdf.is_netcdf_file(filename):
        fields = netcdf.read(filename, external_files=external_files,
                             field=field, _debug=_debug)
    else:
        raise IOError("Can't determine format of file {}".format(filename))

    # ----------------------------------------------------------------
    # Return the fields
    # ----------------------------------------------------------------
    return fields
#--- End: def
