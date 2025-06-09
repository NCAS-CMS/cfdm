from ...quantization import Quantization

CODE0 = {
    # Physically meaningful and corresponding to constructs
    "Cell measures variable": 100,
    "cell_measures attribute": 101,
    "Bounds variable": 200,
    "bounds attribute": 201,
    "Ancillary variable": 120,
    "ancillary_variables attribute": 121,
    "Formula terms variable": 130,
    "formula_terms attribute": 131,
    "Bounds formula terms variable": 132,
    "Bounds formula_terms attribute": 133,
    "Auxiliary/scalar coordinate variable": 140,
    "coordinates attribute": 141,
    "grid mapping variable": 150,
    "grid_mapping attribute": 151,
    "Grid mapping coordinate variable": 152,
    "Cell method interval": 160,
    # Purely structural
    "Compressed dimension": 300,
    "compress attribute": 301,
    "Instance dimension": 310,
    "instance_dimension attribute": 311,
    "Count dimension": 320,
    "count_dimension attribute": 321,
}

CODE1 = {
    "is incorrectly formatted": 2,
    "is not in file": 3,
    "spans incorrect dimensions": 4,
    (
        "is not in file nor referenced by the "
        "external_variables global attribute"
    ): 5,
    "has incompatible terms": 6,
    "that spans the vertical dimension has no bounds": 7,
    (
        "that does not span the vertical dimension is "
        "inconsistent with the formula_terms of the "
        "parametric coordinate variable"
    ): 8,
}

# --------------------------------------------------------------------
# NetCDF formats
# --------------------------------------------------------------------
# NetCDF file magic numbers
NETCDF_MAGIC_NUMBERS = (
    21382211,
    1128547841,
    1178880137,
    38159427,
    88491075,
)

# NetCDF-3 file formats
NETCDF3_FMTS = (
    "NETCDF3_CLASSIC",
    "NETCDF3_64BIT",
    "NETCDF3_64BIT_OFFSET",
    "NETCDF3_64BIT_DATA",
)

# NetCDF-4 file formats
NETCDF4_FMTS = ("NETCDF4", "NETCDF4_CLASSIC")

# --------------------------------------------------------------------
# Quantization
# --------------------------------------------------------------------
# Map CF quantization algorithms to netCDF4 quantize_mode keyword
# values
NETCDF_QUANTIZE_MODES = {
    "bitgroom": "BitGroom",
    "bitround": "BitRound",
    "digitround": "DigitRound",
    "granular_bitround": "GranularBitRound",
}

# Map CF quantization algorithms to netCDF-C library quantization
# attributes
NETCDF_QUANTIZATION_PARAMETERS = {
    "bitgroom": "_QuantizeBitGroomNumberOfSignificantDigits",
    "bitround": "_QuantizeBitRoundNumberOfSignificantBits",
    "digitround": "_QuantizeDigitRoundNumberOfSignificantDigits",
    "granular_bitround": "_QuantizeGranularBitRoundNumberOfSignificantDigits",
}

# Map CF quantization algorithms to CF quantization parameters (CF
# section 8.4.2. Per-variable quantization attributes)
CF_QUANTIZATION_PARAMETERS = Quantization.algorithm_parameters()

# Map CF quantization parameters to their upper limits for each data
# type (CF section 8.4.2. Per-variable quantization attributes)
CF_QUANTIZATION_PARAMETER_LIMITS = {
    "quantization_nsd": {"f4": 7, "f8": 15},
    "quantization_nsb": {"f4": 23, "f8": 52},
}
