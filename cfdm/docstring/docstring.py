'''Define docstring substitutions.

Text to be replaced is specified as a key in the returned dictionary,
with the replacement text defined by the corresponding value.

Keys must be `str` or `re.Pattern` objects.

If a key is a `str` then the corresponding value must be a string.
    
If a key is a `re.Pattern` object then the corresponding value must be
a string or a callable, as accepted by the `re.Pattern.sub` method.

Special docstring subtitutions, as defined by a classes
`_special_docstring_substitutions` method, may be used in the
replacement text, and will be substituted as ususal.

.. versionaddedd:: (cfdm) 1.8.7.0

'''
_docstring_substitution_definitions = {
    # ----------------------------------------------------------------
    # General docstring susbstitutions
    # ----------------------------------------------------------------
    '{{equals tolerance}}':
    '''Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences) are
    positive, typically very small numbers. See the *atol* and *rtol*
    parameters.''',

    '{{equals compression}}':
    '''Any compression is ignored by default, with only the arrays in
    their uncompressed forms being compared. See the
    *ignore_compression* parameter.''',

    '{{equals netCDF}}':
    '''NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked.''',

    # ----------------------------------------------------------------
    # Parameter description substitutions
    # ----------------------------------------------------------------

    # atol
    '{{atol: float, optional}}':
            '''atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `{{package}}.atol`
            function.''',

    # rtol
    '{{rtol: float, optional}}':
            '''rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `{{package}}.rtol`
            function.''',

    # ignore_compression
    '{{ignore_compression: `bool`, optional}}':
            '''ignore_compression: `bool`, optional
            If False then the compression type and, if applicable, the
            underlying compressed arrays must be the same, as well as
            the arrays in their uncompressed forms. By default only
            the the arrays in their uncompressed forms are
            compared.''',

    # ignore_data_type
    '{{ignore_data_type: `bool`, optional}}':
            '''ignore_data_type: `bool`, optional
            If True then ignore the data types in all numerical
            comparisons. By default different numerical data types
            imply inequality, regardless of whether the elements are
            within the tolerance for equality.''',
           
    # ignore_type
    '{{ignore_type: `bool`, optional}}':
            '''ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another `{{class}}` instance, or a
            subclass of one. If *ignore_type* is True then
            ``{{package}}.{{class}}(source=other)`` is tested, rather
            than the ``other`` defined by the *other* parameter.''',
            
    # inplace
    '{{inplace: `bool`, optional}}':
            '''inplace: `bool`, optional
            If True then do the operation in-place and return `None`.''',

    # verbose
    '{{verbose: `int` or `str` or `None`, optional}}':
            """verbose: `int` or `str` or `None`, optional
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
            verbosity, with the exception of ``-1`` as a special case
            of maximal and extreme verbosity.

            Otherwise, if `None` (the default value), output messages
            will be shown according to the value of the
            `{{package}}.log_level` setting.

            Overall, the higher a non-negative integer or equivalent
            string that is set (up to a maximum of ``3``/``'DETAIL'``)
            for increasing verbosity, the more description that is
            printed to convey information about the operation.""",
    
}
