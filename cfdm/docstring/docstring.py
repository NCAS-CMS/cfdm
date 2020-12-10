'''Define docstring substitutions.

Text to be replaced is specified as a key in the returned dictionary,
with the replacement text defined by the corresponding value.

Special docstring substitutions, as defined by a class's
`_docstring_special_substitutions` method, may be used in the
replacement text, and will be substituted as usual.

Replacement text may contain other non-special substitutions.

.. note:: The values are only checked once for embedded non-special
          substitutions, so if the embedded substitution itself
          contains a non-special substitution then the latter will
          *not* be replaced. This restriction is to prevent the
          possibility of infinite recursion.

Keys must be `str` or `re.Pattern` objects:

* If a key is a `str` then the corresponding value must be a string.

* If a key is a `re.Pattern` object then the corresponding value must
  be a string or a callable, as accepted by the `re.Pattern.sub`
  method.

.. versionaddedd:: (cfdm) 1.8.7.0

'''
from ..core import CF


_docstring_substitution_definitions = {
    # ----------------------------------------------------------------
    # General docstring susbstitutions
    # ----------------------------------------------------------------
    '{{VN}}': CF(),

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

    '{{netCDF variable}}':
    '''The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.''',

    # properties: `dict`, optional
    '{{init properties: `dict`, optional}}':
    '''properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.''',

    # ----------------------------------------------------------------
    # Parameter description substitutions
    # ----------------------------------------------------------------
    # atol
    '{{atol: number, optional}}':
    '''atol: number, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the
            `{{package}}.atol` function.''',

    # data_name
    '{{data_name: `str`, optional}}':
    '''data_name: `str`, optional
            The name of the construct's `Data` instance created by the
            returned commands.

            *Parameter example:*
              ``name='data1'``''',

    # header
    '{{header: `bool`, optional}}':
    '''header: `bool`, optional
            If False then do not output a comment describing the
            components.''',

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

    # ignore_fill_value
    '{{ignore_fill_value: `bool`, optional}}':
    '''ignore_fill_value: `bool`, optional
             If True then the ``_FillValue`` and ``missing_value``
            properties are omitted from the comparison.''',

    # ignore_properties
    '{{ignore_properties: sequence of `str`, optional}}':
    '''ignore_properties: sequence of `str`, optional
            The names of properties to omit from the comparison.''',

    # inplace
    '{{inplace: `bool`, optional}}':
    '''inplace: `bool`, optional
            If True then do the operation in-place and return `None`.''',

    # ignore_type
    '{{ignore_type: `bool`, optional}}':
    '''ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another `{{class}}` instance, or a
            subclass of one. If *ignore_type* is True then
            ``{{package}}.{{class}}(source=other)`` is tested, rather
            than the ``other`` defined by the *other* parameter.''',

    # indent
    '{{indent: `int`, optional}}':
    '''indent: `int`, optional
           Indent each line by this many spaces. By default no
            indentation is applied. Ignored if *string* is False.''',

    # name
    '{{name: `str`, optional}}':
    '''name: `str`, optional
            The name of the `{{class}}` instance created by the
            returned commands.

            *Parameter example:*
              ``name='var1'``''',

    # namespace
    '{{namespace: `str`, optional}}':
    '''namespace: `str`, optional
            The name space containing classes of the {{package}}
            package. This is prefixed to the class name in commands
            that instantiate instances of {{package}} objects. By default,
            or if `None`, the name space is assumed to be consistent
            with {{package}} being imported as ``import {{package}}``.

            *Parameter example:*
              If {{package}} was imported as ``import {{package}} as xyz``
              then set ``namespace='xyz'``

            *Parameter example:*
              If {{package}} was imported as ``from {{package}} import *``
              then set ``namespace=''``''',

    # representative_data
    '{{representative_data: `bool`, optional}}':
    '''representative_data: `bool`, optional
            Return one-line representations of `Data` instances, which
            are not executable code but prevent the data being
            converted in its entirety to a string representation.''',

    # rtol
    '{{rtol: number, optional}}':
    '''rtol: number, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the
            `{{package}}.rtol` function.''',

    # string
    '{{string: `bool`, optional}}':
    '''string: `bool`, optional
            If False then return each command as an element of a
            `list`. By default the commands are concatenated into
            a string, with a new line inserted between each command.''',

    # verbose
    '{{verbose: `int` or `str` or `None`, optional}}':
    '''verbose: `int` or `str` or `None`, optional
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
            printed to convey information about the operation.''',

    # ----------------------------------------------------------------
    # Returns descriptions
    # ----------------------------------------------------------------
    '{{returns creation_commands}}':
    '''`str` or `list`
            The commands in a string, with a new line inserted between
            each command. If *string* is False then the separate
            commands are returned as each element of a `list`.''',

    '{{returns dump}}':
    '''`str` or `None`
            The description. If *display* is True then the description
            is printed and `None` is returned. Otherwise the
            description is returned as a string.''',
}
