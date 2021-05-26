"""Define docstring substitutions.

Text to be replaced is specified as a key in the returned dictionary,
with the replacement text defined by the corresponding value.

Special docstring substitutions, as defined by a class's
`_docstring_special_substitutions` method, may be used in the
replacement text, and will be substituted as usual.

Replacement text may not contain other non-special substitutions.

Keys must be `str` or `re.Pattern` objects:

* If a key is a `str` then the corresponding value must be a string.

* If a key is a `re.Pattern` object then the corresponding value must
  be a string or a callable, as accepted by the `re.Pattern.sub`
  method.

.. versionaddedd:: (cfdm) 1.8.7.0

"""
_docstring_substitution_definitions = {
    # ----------------------------------------------------------------
    # General susbstitutions (not indent-dependent)
    # ----------------------------------------------------------------
    "{{repr}}": "",
    # ----------------------------------------------------------------
    # # Method description susbstitutions (2 levels of indentation)
    # ----------------------------------------------------------------
    # cached: optional
    "{{cached: optional}}": """cached: optional
                If any value other than `None` then return *cached*
                without selecting any constructs.""",
    # todict: `bool`, optional
    "{{todict: `bool`, optional}}": """todict: `bool`, optional
                If True then return a dictionary of constructs keyed
                by their construct identifiers, instead of a
                `Constructs` object. This is a faster option.""",
    # ----------------------------------------------------------------
    # # Method description susbstitutions (3 levels of indentation)
    # ----------------------------------------------------------------
    # axes int examples
    "{{axes int examples}}": """Each axis is identified by its integer position in the
                data. Negative integers counting from the last
                position are allowed.

                *Parameter example:*
                  ``axes=0``

                *Parameter example:*
                  ``axes=-1``

                *Parameter example:*
                  ``axes=[1, -2]``""",
    # default Exception
    "{{default Exception}}": """If set to an `Exception` instance then it will be
                raised instead.""",
    # inplace: `bool`, optional (default True)
    "{{inplace: `bool`, optional (default True)}}": """inplace: `bool`, optional:
                If False then do not do the operation in-place and
                return a new, modified `{{class}}` instance. By
                default the operation is in-place and `None` is
                returned.""",
    # init properties
    "{{init properties: `dict`, optional}}": """properties: `dict`, optional
                Set descriptive properties. The dictionary keys are
                property names, with corresponding values. Ignored if
                the *source* parameter is set.

                Properties may also be set after initialisation with
                the `set_properties` and `set_property` methods.""",
    # init data
    "{{init data: data_like, optional}}": """data: data_like, optional
                Set the data. Ignored if the *source* parameter is
                set.

                {{data_like}}

                The data also may be set after initialisation with the
                `set_data` method.""",
    # init bounds
    "{{init bounds: `Bounds`, optional}}": """bounds: `Bounds`, optional
                Set the bounds array. Ignored if the *source*
                parameter is set.

                The bounds array may also be set after initialisation
                with the `set_bounds` method.""",
    # init geometry
    "{{init geometry: `str`, optional}}": """geometry: `str`, optional
                Set the geometry type. Ignored if the *source*
                parameter is set.

                The geometry type may also be set after initialisation
                with the `set_geometry` method.

                *Parameter example:*
                  ``geometry='polygon'``""",
    # init interior_ring
    "{{init interior_ring: `InteriorRing`, optional}}": """interior_ring: `InteriorRing`, optional
                Set the interior ring variable. Ignored if the
                *source* parameter is set.

                The interior ring variable may also be set after
                initialisation with the `set_interior_ring` method.""",
    # init copy
    "{{init copy: `bool`, optional}}": """copy: `bool`, optional
                If False then do not deep copy input parameters prior
                to initialisation. By default arguments are deep
                copied.""",
    # init source
    "{{init source}}": """Note that if *source* is a `{{class}}` instance then
                ``{{package}}.{{class}}(source=source)`` is equivalent
                to ``source.copy()``.""",
    # data_like
    "{{data_like}}": """A data_like object is any object that can be converted
                to a `Data` object, i.e. `numpy` array_like objects,
                `Data` objects, and {{package}} instances that contain
                `Data` objects.""",
}
