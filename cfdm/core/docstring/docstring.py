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
    '{{repr}}':
    '',
    
    '{{default: optional}}':
            '''default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.''',
}
