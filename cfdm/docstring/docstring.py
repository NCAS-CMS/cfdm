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
    # General substitutions (not indent-dependent)
    # ----------------------------------------------------------------
    #
    # ----------------------------------------------------------------
    # Class description substitutions (1 level of indentation)
    # ----------------------------------------------------------------
    # netCDF variable
    "{{netCDF variable}}": """The netCDF variable name may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups`
    methods.""",
    # netCDF global attributes
    "{{netCDF global attributes}}": """The selection of properties to be written as netCDF global
    attributes may be accessed with the `nc_global_attributes`,
    `nc_clear_global_attributes` and `nc_set_global_attribute`
    methods.""",
    # netCDF group attributes
    "{{netCDF group attributes}}": """The netCDF group attributes may be accessed with the
    `nc_group_attributes`, `nc_clear_group_attributes`,
    `nc_set_group_attribute` and `nc_set_group_attributes` methods.""",
    # netCDF geometry group
    "{{netCDF geometry group}}": """The netCDF geometry variable name and group structure may be
    accessed with the `nc_set_geometry_variable`,
    `nc_get_geometry_variable`, `nc_geometry_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_geometry_variable_groups`
    methods.""",
    # ----------------------------------------------------------------
    # Method description substitutions (2 levels of indentation)
    # ----------------------------------------------------------------
    # equals tolerance
    "{{equals tolerance}}": """Two real numbers ``x`` and ``y`` are considered equal if
        ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on
        absolute differences) and ``rtol`` (the tolerance on relative
        differences) are positive, typically very small numbers. See
        the *atol* and *rtol* parameters.""",
    # equals compression
    "{{equals compression}}": """Any compression is ignored by default, with only the arrays in
        their uncompressed forms being compared. See the
        *ignore_compression* parameter.""",
    # equals netCDF
    "{{equals netCDF}}": """NetCDF elements, such as netCDF variable and dimension names,
        do not constitute part of the CF data model and so are not
        checked.""",
    # netcdf global
    "{{netcdf global}}": """When multiple field or domain constructs are being written to
        the same file, it is only possible to create a netCDF global
        attribute from a property that has identical values for each
        construct. If any field or domain construct's property has a
        different value then the property will not be written as a
        netCDF global attribute, even if it has been selected as such,
        but will appear instead as attributes on the netCDF data
        variables corresponding to each construct.

        The standard description-of-file-contents properties are
        always written as netCDF global attributes, if possible, so
        selecting them is optional.""",
    # unique construct
    "{{unique construct}}": """If zero or two or more constructs are selected then an
        exception is raised, or the *default* parameter is returned.""",
    # ----------------------------------------------------------------
    # Method description substitutions (3 levels of indentataion)
    # ----------------------------------------------------------------
    # init properties: `dict`, optional
    "{{init properties: `dict`, optional}}": """properties: `dict`, optional
                Set descriptive properties. The dictionary keys are
                property names, with corresponding values. Ignored if
                the *source* parameter is set.

                Properties may also be set after initialisation with
                the `set_properties` and `set_property` methods.""",
    # atol: number, optional
    "{{atol: number, optional}}": """atol: number, optional
                The tolerance on absolute differences between real
                numbers. The default value is set by the
                `{{package}}.atol` function.""",
    # data_name: `str`, optional
    "{{data_name: `str`, optional}}": """data_name: `str`, optional
                The name of the construct's `Data` instance created by
                the returned commands.

                *Parameter example:*
                  ``name='data1'``""",
    # header: `bool`, optional
    "{{header: `bool`, optional}}": """header: `bool`, optional
                If False then do not output a comment describing the
                components.""",
    # ignore_compression: `bool`, optional
    "{{ignore_compression: `bool`, optional}}": """ignore_compression: `bool`, optional
                If False then the compression type and, if applicable,
                the underlying compressed arrays must be the same, as
                well as the arrays in their uncompressed forms. By
                default only the the arrays in their uncompressed
                forms are compared.""",
    # ignore_data_type: `bool`, optional
    "{{ignore_data_type: `bool`, optional}}": """ignore_data_type: `bool`, optional
                If True then ignore the data types in all numerical
                comparisons. By default different numerical data types
                imply inequality, regardless of whether the elements
                are within the tolerance for equality.""",
    # ignore_fill_value
    "{{ignore_fill_value: `bool`, optional}}": """ignore_fill_value: `bool`, optional
                If True then all ``_FillValue`` and ``missing_value``
                properties are omitted from the comparison.""",
    # ignore_properties
    "{{ignore_properties: sequence of `str`, optional}}": """ignore_properties: sequence of `str`, optional
                The names of properties to omit from the
                comparison.""",
    # inplace
    "{{inplace: `bool`, optional}}": """inplace: `bool`, optional
                If True then do the operation in-place and return
                `None`.""",
    # ignore_type
    "{{ignore_type: `bool`, optional}}": """ignore_type: `bool`, optional
                Any type of object may be tested but, in general,
                equality is only possible with another `{{class}}`
                instance, or a subclass of one. If *ignore_type* is
                True then ``{{package}}.{{class}}(source=other)`` is
                tested, rather than the ``other`` defined by the
                *other* parameter.""",
    # indent
    "{{indent: `int`, optional}}": """indent: `int`, optional
                Indent each line by this many spaces. By default no
                indentation is applied. Ignored if *string* is
                False.""",
    # name
    "{{name: `str`, optional}}": """name: `str`, optional
                The name of the `{{class}}` instance created by the
                returned commands.

                *Parameter example:*
                  ``name='var1'``""",
    # namespace
    "{{namespace: `str`, optional}}": """namespace: `str`, optional
                The name space containing classes of the {{package}}
                package. This is prefixed to the class name in
                commands that instantiate instances of {{package}}
                objects. By default, or if `None`, the name space is
                assumed to be consistent with {{package}} being
                imported as ``import {{package}}``.

                *Parameter example:*
                  If {{package}} was imported as ``import {{package}}
                  as xyz`` then set ``namespace='xyz'``

                *Parameter example:*
                  If {{package}} was imported as ``from {{package}}
                  import *`` then set ``namespace=''``""",
    # representative_data
    "{{representative_data: `bool`, optional}}": """representative_data: `bool`, optional
                Return one-line representations of `Data` instances,
                which are not executable code but prevent the data
                being converted in its entirety to a string
                representation.""",
    # rtol
    "{{rtol: number, optional}}": """rtol: number, optional
                The tolerance on relative differences between real
                numbers. The default value is set by the
                `{{package}}.rtol` function.""",
    # string
    "{{string: `bool`, optional}}": """string: `bool`, optional
                If False then return each command as an element of a
                `list`. By default the commands are concatenated into
                a string, with a new line inserted between each
                command.""",
    # verbose
    "{{verbose: `int` or `str` or `None`, optional}}": """verbose: `int` or `str` or `None`, optional
                If an integer from ``-1`` to ``3``, or an equivalent
                string equal ignoring case to one of:

                * ``'DISABLE'`` (``0``)
                * ``'WARNING'`` (``1``)
                * ``'INFO'`` (``2``)
                * ``'DETAIL'`` (``3``)
                * ``'DEBUG'`` (``-1``)

                set for the duration of the method call only as the
                minimum cut-off for the verboseness level of displayed
                output (log) messages, regardless of the
                globally-configured `{{package}}.log_level`. Note that
                increasing numerical value corresponds to increasing
                verbosity, with the exception of ``-1`` as a special
                case of maximal and extreme verbosity.

                Otherwise, if `None` (the default value), output
                messages will be shown according to the value of the
                `{{package}}.log_level` setting.

                Overall, the higher a non-negative integer or
                equivalent string that is set (up to a maximum of
                ``3``/``'DETAIL'``) for increasing verbosity, the more
                description that is printed to convey information
                about the operation.""",
    # construct selection identity
    "{{construct selection identity}}": """A construct has a number of string-valued identities
                defined by its `!identities` method, and is selected
                if any of them match the *identity*
                parameter. *identity* may be a string that equals one
                of a construct's identities; or a `re.Pattern` object
                that matches one of a construct's identities via
                `re.search`.

                Note that in the output of a `dump` method or `print`
                call, a metadata construct is always described by one
                of its identities, and so this description may always
                be used as an *identity* value.""",
    # domain axis selection identity
    "{{domain axis selection identity}}": """A domain axis construct has a number of string-valued
                identities (defined by its `!identities` method) and
                is selected if any of them match the *identity*
                parameter.  *identity* may be a string that equals one
                of a construct's identities; or a `re.Pattern` object
                that matches one of a construct's identities via
                `re.search`.""",
    # returns creation_commands
    "{{returns creation_commands}}": """`str` or `list`
                The commands in a string, with a new line inserted
                between each command. If *string* is False then the
                separate commands are returned as each element of a
                `list`.""",
    # returns dump
    "{{returns dump}}": """`str` or `None`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.""",
    # generator: `bool`, optional
    "{{generator: `bool`, optional}}": """generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list. This can give improved performance
                if iteration through the generator can be stopped
                before all identities have been computed.

                .. versionadded:: (cfdm) 1.8.9.0""",
    # filter_kwargs: optional
    "{{filter_kwargs: optional}}": """filter_kwargs: optional
                Keyword arguments as accepted by `Constructs.filter`
                that define additional construct selection
                criteria.""",
    # Returns constructs
    "{{Returns constructs}}": """
                The selected constructs in a new `Constructs` object,
                unless modified by any *filter_kwargs* parameters.""",
    # ----------------------------------------------------------------
    # Method description susbstitutions (4 levels of indentataion)
    # ----------------------------------------------------------------
    # string value match
    "{{value match}}": """A value may be any object that can match via the
                ``==`` operator, or a `re.Pattern` object that matches
                via its `~re.Pattern.search` method.""",
    # displayed identity
    "{{displayed identity}}": """Note that in the output of a `dump` method or `print`
                call, a construct is always described by an identity
                that will select it.""",
}
