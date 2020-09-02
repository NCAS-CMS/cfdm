'''Define docstring substitutions.

Text to be replaced is specified as a key in the returned dictionary,
with the replacement text defined by the corresponding value.

Keys must be `str` or `re.Pattern` objects:

* If a key is a `str` then the corresponding value must be a string.

* If a key is a `re.Pattern` object then the corresponding value must
  be a string or a callable, as accepted by the `re.Pattern.sub`
  method.

Special docstring subtitutions, as defined by a class's
`_docstring_special_substitutions` method, may be used in the
replacement text, and will be substituted as ususal.

.. versionaddedd:: (cfdm) 1.8.7.0

'''
_docstring_substitution_definitions = {
    '{{repr}}':
    '',

    # ----------------------------------------------------------------
    # Keyword parameter descriptions
    # ----------------------------------------------------------------

    # default
    '{{default: optional}}':
    '''default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.''',

    # init properties
    '{{init properties: `dict`, optional}}':
    '''properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.''',

    # init data
    '{{init data: `Data`, optional}}':
    '''data: `Data`, optional
            Set the data. Ignored if the *source* parameter is set.

            The data also may be set after initialisation with the
            `set_data` method.''',

    # init bounds
    '{{init bounds: `Bounds`, optional}}':
    '''bounds: `Bounds`, optional
            Set the bounds array. Ignored if the *source* parameter is
            set.

            The bounds array may also be set after initialisation with
            the `set_bounds` method.''',

    # init geometry
    '{{init geometry: `str`, optional}}':
    '''geometry: `str`, optional
            Set the geometry type. Ignored if the *source* parameter
            is set.

            The geometry type may also be set after initialisation
            with the `set_geometry` method.

            *Parameter example:*
               ``geometry='polygon'``''',

    # init interior_ring
    '{{init interior_ring: `InteriorRing`, optional}}':
    '''interior_ring: `InteriorRing`, optional
            Set the interior ring variable. Ignored if the *source*
            parameter is set.

            The interior ring variable may also be set after
            initialisation with the `set_interior_ring` method.''',

    # init copy
    '{{init copy: `bool`, optional}}':
    '''copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.''',

}
