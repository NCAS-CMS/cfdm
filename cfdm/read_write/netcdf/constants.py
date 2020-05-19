_CODE0 = {
        # Physically meaningful and corresponding to constructs
        'Cell measures variable' : 100,
        'cell_measures attribute': 101,

        'Bounds variable'        : 200,
        'bounds attribute'       : 201,

        'Ancillary variable': 120,
        'ancillary_variables attribute': 121,

        'Formula terms variable': 130,
        'formula_terms attribute': 131,
        'Bounds formula terms variable': 132,
        'Bounds formula_terms attribute': 133,

        'Auxiliary/scalar coordinate variable': 140,
        'coordinates attribute': 141,

        'grid mapping variable': 150,
        'grid_mapping attribute' : 151,
        'Grid mapping coordinate variable': 152,

        'Cell method interval': 160,

        # Purely structural
        'Compressed dimension': 300,
        'compress attribute': 301,
        'Instance dimension':310,
        'instance_dimension attribute':311,
        'Count dimension': 320,
        'count_dimension attribute': 321,
    }

_CODE1 = {
        'is incorrectly formatted': 2,
        'is not in file': 3,
        'spans incorrect dimensions': 4,
        'is not in file nor referenced by the external_variables global attribute': 5,
        'has incompatible terms': 6,

    'that spans the vertical dimension has no bounds': 7,
    'that does not span the vertical dimension is inconsistent with the formula_terms of the parametric coordinate variable': 8,
    }

# --------------------------------------------------------------------
# Recognised netCDF file magic numbers
# --------------------------------------------------------------------
MAGIC_NUMBER = (21382211,
                1128547841,
                1178880137,
                38159427)

## --------------------------------------------------------------------
## Datum-defining parameters names
## --------------------------------------------------------------------
#datum_parameters = ('earth_radius',
#                    'geographic_crs_name',
#                    'geoid_name',
#                    'geopotential_datum_name',
#                    'horizontal_datum_name',
#                    'inverse_flattening',
#                    'longitude_of_prime_meridian',
#                    'prime_meridian_name',
#                    'reference_ellipsoid_name',
#                    'semi_major_axis',
#                    'semi_minor_axis',
#                    'towgs84',
#)
#
## --------------------------------------------------------------------
## Mapping of each coordinate reference canonical name to the
## coordinates to which it applies. The coordinates are defined by
## their standard names.
##
## A coordiante reference canonical name is either the value of the
## grid_mapping_name attribute of a grid mapping variable
## (e.g. 'lambert_azimuthal_equal_area'), or the standard name of a
## vertical coordinate variable with a formula_terms attribute
## (e.g. ocean_sigma_coordinate').
## --------------------------------------------------------------------
#coordinate_reference_coordinates = {
#    'albers_conical_equal_area'                  : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'azimuthal_equidistant'                      : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'geostationary'                              : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'lambert_azimuthal_equal_area'               : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'lambert_conformal_conic'                    : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'lambert_cylindrical_equal_area'             : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'latitude_longitude'                         : ('latitude',
#                                                    'longitude',),
#    'mercator'                                   : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'orthographic'                               : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'polar_stereographic'                        : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'rotated_latitude_longitude'                 : ('grid_latitude',
#                                                    'grid_longitude',
#                                                    'latitude',
#                                                    'longitude',),
#    'sinusoidal'                                 : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'stereographic'                              : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'transverse_mercator'                        : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'vertical_perspective'                       : ('projection_x_coordinate',
#                                                    'projection_y_coordinate',
#                                                    'latitude',
#                                                    'longitude',),
#    'atmosphere_ln_pressure_coordinate'          : ('atmosphere_ln_pressure_coordinate',),
#    'atmosphere_sigma_coordinate'                : ('atmosphere_sigma_coordinate',),
#    'atmosphere_hybrid_sigma_pressure_coordinate': ('atmosphere_hybrid_sigma_pressure_coordinate',),
#    'atmosphere_hybrid_height_coordinate'        : ('atmosphere_hybrid_height_coordinate',),
#    'atmosphere_sleve_coordinate'                : ('atmosphere_sleve_coordinate',),
#    'ocean_sigma_coordinate'                     : ('ocean_sigma_coordinate',),
#    'ocean_s_coordinate'                         : ('ocean_s_coordinate',),
#    'ocean_sigma_z_coordinate'                   : ('ocean_sigma_z_coordinate',),
#    'ocean_double_sigma_coordinate'              : ('ocean_double_sigma_coordinate',),
#}
#
## --------------------------------------------------------------------
## Description of file contents properties
## --------------------------------------------------------------------
#description_of_file_contents_attributes = (
#    'comment',
#    'Conventions',
#    'featureType',
#    'history',
#    'institution',
#    'references',
#    'source',
#    'title',
#)
#
## --------------------------------------------------------------------
## Cell method qualifiers
## --------------------------------------------------------------------
#cell_method_qualifiers = set((
#    'within',
#    'where',
#    'over',
#    'interval',
#    'comment',
#))
#
## --------------------------------------------------------------------
## Geometry types
## --------------------------------------------------------------------
#geometry_types = set((
#    'point',
#    'line',
#    'polygon',
#))
