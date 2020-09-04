import inspect
import re


class DocstringRewriteMeta(type):
    '''Modify docstrings.

    **Method**

    To do this, we intercede before the class is created and modify
    the docstrings of the attributes defined on the class.

    Inherited methods are also modified. We cannot simply modify the
    docstrings of inherited methods, because then the parent classes'
    methods will have the wrong docstring. Instead, we must actually
    copy the functions, and then modify the docstring.

    Special treatment is given to methods decorated with @property,
    @staticmethod and @classmethod, as well as user-defined
    decorations.

    .. versionadded:: (cfdm) 1.8.7.0

    '''
    # Based on
    # http://www.jesshamrick.com/2013/04/17/rewriting-python-docstrings-with-a-metaclass/

    def __new__(cls, class_name, parents, attrs):
        # ------------------------------------------------------------
        # Combine the docstring substitutions from all classes in the
        # inheritance tree. The value for a key that occurs in
        # multiple classes will be taken from the class closest to the
        # child class.
        # ------------------------------------------------------------
        docstring_rewrite = {}

        for parent in parents[::-1]:
            parent_docstring_rewrite = getattr(
                parent, '_docstring_substitutions', None)
            if parent_docstring_rewrite is not None:
                docstring_rewrite.update(parent_docstring_rewrite(parent))
            else:
                parent_docstring_rewrite = getattr(
                    parent, '__docstring_substitutions__', None)
                if parent_docstring_rewrite is not None:
                    docstring_rewrite.update(parent_docstring_rewrite(None))
        # --- End: for

        class_docstring_rewrite = attrs.get(
            '__docstring_substitutions__', None)
        if class_docstring_rewrite is not None:
            docstring_rewrite.update(class_docstring_rewrite(None))

        special = DocstringRewriteMeta._docstring_special_substitutions()
        for key in special:
            if key in docstring_rewrite:
                raise ValueError(
                    "Can't use {!r} as a user-defined "
                    "docstring substitution.".format(key)
                )
        # --- End: for

        # ------------------------------------------------------------
        # Find the package depth
        # ------------------------------------------------------------
        package_depth = 0
        for parent in parents[::-1]:
            parent_depth = getattr(
                parent, '_docstring_package_depth', None)
            if parent_depth is not None:
                package_depth = parent_depth(parent)
            else:
                parent_depth = getattr(
                    parent, '__docstring_package_depth__', None)
                if parent_depth is not None:
                    package_depth = parent_depth(None)
        # --- End: for

        class_depth = attrs.get('__docstring_package_depth__', None)
        if class_depth is not None:
            package_depth = class_depth(None)

        package_depth += 1

        module = attrs['__module__'].split('.')
        package_name = '.'.join(module[:package_depth])

        # ------------------------------------------------------------
        # Find which methods to exclude
        # ------------------------------------------------------------
        method_exclusions = []
        for parent in parents[::-1]:
            parent_exclusions = getattr(
                parent, '_docstring_method_exclusions', None)
            if parent_exclusions is not None:
                method_exclusions.extend(parent_exclusions(parent))
            else:
                parent_exclusions = getattr(
                    parent, '__docstring_method_exclusions__', None)
                if parent_exclusions is not None:
                    method_exclusions.extend(parent_exclusions(None))
        # --- End: for

        class_exclusions = attrs.get('__docstring_method_exclusions__', None)
        if class_exclusions is not None:
            method_exclusions.extend(class_exclusions(None))

        method_exclusions = set(method_exclusions)

        for attr_name, attr in attrs.items():

            # Skip special methods that aren't functions
            if (
                    attr_name.startswith('__') and
                    not inspect.isfunction(attr)
            ):
                continue

            # Skip methods without docstrings
            if not hasattr(attr, '__doc__'):
                continue

            if attr_name in method_exclusions:
                continue

            # @property
            if hasattr(attr, 'fget'):
                # Note that here inspect.isroutine(attr) is False for
                # @property methods (but this is not the case for
                # properties in the parent classes).
                DocstringRewriteMeta._docstring_update(package_name,
                                                       class_name,
                                                       attr,
                                                       attr_name,
                                                       docstring_rewrite)
                continue

            # Still here?
            if not inspect.isroutine(attr):
                continue

            # Still here?
            is_classmethod = False
            is_staticmethod = False

            # Find out if the method is a classmethod (the
            # inspect.ismethod technique doesn't work for this class)
            if isinstance(attr, classmethod):
                is_classmethod = True
            elif isinstance(attr, staticmethod):
                is_staticmethod = True

            is_wrapped = hasattr(attr, '__wrapped__')
            if is_wrapped:
                wrapper = attr
                attr = attr.__wrapped__

            if is_classmethod or is_staticmethod:
                f = getattr(attr, '__func__', attr)

                # Copy the method
                attr = type(f)(f.__code__, f.__globals__,
                               f.__name__, f.__defaults__,
                               f.__closure__)

                # Make sure that the keyword argument defaults are set
                # correctly. In general they will be, but not if there
                # is a variable number of positional arguments, such
                # as in: def foo(self, *x, y=None)
                attr.__kwdefaults__ = f.__kwdefaults__

            # Update docstring
            DocstringRewriteMeta._docstring_update(package_name,
                                                   class_name,
                                                   attr,
                                                   attr_name,
                                                   docstring_rewrite)

            # Redecorate
            if is_classmethod:
                attrs[attr_name] = classmethod(attr)

            if is_staticmethod:
                attrs[attr_name] = staticmethod(attr)

            if is_wrapped:
                wrapper.__doc__ = attr.__doc__
                wrapper.__wrapped__ = attr
                attrs[attr_name] = wrapper
        # --- End: for

        # ------------------------------------------------------------
        # TODO
        # ------------------------------------------------------------
        for parent in parents:

            for attr_name in dir(parent):

                if attr_name in attrs:
                    # We already have this method from higher up in
                    # the method resolution order, so do not overwrite
                    # it and move on to to the next method.
                    continue

                # ----------------------------------------------------
                # Get the original method, copy it, update the
                # docstring, and put the mosfied copy back into the
                # parent class.
                # ----------------------------------------------------
                original_f = getattr(parent, attr_name)

                # Skip special methods that aren't functions
                if (
                        attr_name.startswith('__') and
                        not inspect.isfunction(original_f)
                ):
                    continue

                if attr_name in method_exclusions:
                    continue

                is_classmethod = False
                is_staticmethod = False
                is_wrapped = False

                try:
                    if hasattr(original_f, 'fget'):
                        # The original function is decorated with
                        # @property
                        attr = type(original_f)(original_f.fget,
                                                original_f.fset,
                                                original_f.fdel)
                    else:
                        if not inspect.isroutine(original_f):
                            continue

                        if inspect.ismethod(original_f):
                            is_classmethod = True
                        elif isinstance(parent.__dict__.get(attr_name),
                                        staticmethod):
                            is_staticmethod = True

                        is_wrapped = hasattr(original_f, '__wrapped__')

                        f = getattr(original_f, '__func__', original_f)

                        # Copy the method
                        attr = type(f)(f.__code__, f.__globals__,
                                       f.__name__, f.__defaults__,
                                       f.__closure__)

                        # Make sure that the keyword argument defaults
                        # are set correctly. In general they will be,
                        # but not if there is a variable number of
                        # positional arguments, such as in: def
                        # foo(self, *x, y=None)
                        attr.__kwdefaults__ = f.__kwdefaults__

                        if is_wrapped:
                            attr.__doc__ = original_f.__doc__
                    # --- End: if

                    # Update the docstring
                    DocstringRewriteMeta._docstring_update(package_name,
                                                           class_name,
                                                           attr,
                                                           attr_name,
                                                           docstring_rewrite)

                    # Register a classmethod
                    if is_classmethod:
                        attr = classmethod(attr)

                    # Register a classmethod
                    if is_staticmethod:
                        attr = staticmethod(attr)

                    if is_wrapped:
                        # Copy the wrapper and update its wrapped
                        # function
                        wrapper = type(original_f)(
                            original_f.__code__,
                            original_f.__globals__,
                            original_f.__name__,
                            original_f.__defaults__,
                            original_f.__closure__)

                        wrapper.__wrapped__ = attr
                        wrapper.__doc__ = attr.__doc__
                        attr = wrapper

                    # Put the modified method back into the parent
                    # class
                    attrs[attr_name] = attr

                except Exception as error:
                    raise RuntimeError(str(error) + ': ' +
                                       '.'.join([parent.__name__,
                                                 attr_name]))
        # --- End: for

        # Create the class
        return super().__new__(cls, class_name, parents, attrs)

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    @classmethod
    def _docstring_special_substitutions(cls):
        '''Return the special docstring subtitutions.

    ``{{class}}`` is replaced by the name of the class.

    ``{{package}}`` is replaced by the name of the package, as defined
    by the first N ``.`` separated fields of the class's `__module__`
    attribute, where is N determined by `_docstring_package_depth`.

    .. versionadded:: (cfdm) 1.8.7.0

    .. seealso:: `_docstring_package_depth`,
                 `_docstring_method_exclusions`,
                 `_docstring_substitutions`,
                 `__docstring_substitutions__`,
                 `__docstring_package_depth__`
                 `__docstring_method_exclusions__`

    :Returns:

        `tuple`
            The special docstring substitution identifiers.

        '''
        return (
            '{{class}}',
            '{{package}}',
        )

    @staticmethod
    def _docstring_substitutions(cls):
        '''Return the docstring substitutions that apply to methods of the
    given class.

    Text to be replaced is specified as a key in the returned
    dictionary, with the replacement text defined by the corresponding
    value.

    A key must be either a `str` or a `re.Pattern` object.

    If a key is a `str` then the corresponding value must be a string.

    If a key is a `re.Pattern` object then the corresponding value
    must be a string or a callable, as accepted by the
    `re.Pattern.sub` method.

    Special docstring subtitutions, as defined by
    `_docstring_special_substitutions`, are applied to the replacement
    text.

    .. versionadded:: (cfdm) 1.8.7.0

    .. seealso:: `_docstring_special_substitutions`,
                 `_docstring_package_depth`,
                 `_docstring_method_exclusions`,
                 `__docstring_substitutions__`,
                 `__docstring_package_depth__`
                 `__docstring_method_exclusions__`

    :Parameters:

        cls: class
            The class.

    :Returns:

        `dict`
            The docstring substitutions. A dictionary key matches text
            in the docstrings, with a corresponding value its
            replacement.

        '''
        out = {}

        for klass in cls.__bases__[::-1]:
            d_s = getattr(klass, '_docstring_substitutions', None)
            if d_s is not None:
                out.update(d_s(klass))
            else:
                d_s = getattr(klass, '__docstring_substitutions__', None)
                if d_s is not None:
                    out.update(d_s(None))
        # --- End: for

        d_s = getattr(cls, '__docstring_substitutions__', None)
        if d_s is not None:
            out.update(d_s(None))

        return out

    @staticmethod
    def _docstring_package_depth(cls):
        '''Return the package depth, N, for {{package}} docstring
    substitutions for the given class.

    In docstrings, ``{{package}}`` is replaced by the name of the
    package, as defined by the first N+1 ``.`` separated fields of the
    class's `__module__` attribute.

    N defaults to 0, but may be set to any non-negative integer, M, by
    creating a `__docstring_package_depth__` method that returns M.

    .. versionadded:: (cfdm) 1.8.7.0

    .. seealso:: `_docstring_special_substitutions`,
                 `_docstring_substitutions`,
                 `_docstring_method_exclusions`,
                 `__docstring_substitutions__`,
                 `__docstring_package_depth__`,
                 `__docstring_method_exclusions__`

    :Parameters:

        cls: class
            The class.

    :Returns:

        `int`
            The package depth.

        '''
        out = 0

        for klass in cls.__bases__[::-1]:
            d_s = getattr(klass, '_docstring_package_depth', None)
            if d_s is not None:
                out = d_s(klass)
            else:
                d_s = getattr(klass, '__docstring_package_depth__', None)
                if d_s is not None:
                    out = d_s(None)
        # --- End: for

        d_s = getattr(cls, '__docstring_package_depth__', None)
        if d_s is not None:
            out = d_s(None)

        return out

    @staticmethod
    def _docstring_method_exclusions(cls):
        '''Return the names of methods to exclude from docstring substitutions
    for the given class.

    Exclusions for a class may be defined by creating a
    `__docstring_method_exclusions__` method that returns the sequence
    of names of methods to be excluded. These exclusions will also
    apply to any child classes.

    Exclsusions may be defined for any reason, but in particular may
    be required if a method has a non-rewriteable docstring. An
    example of method that has a non-rewritable docstring is when the
    method is a 'method_descriptor' object, such as `list.append`: any
    class that inherits such such a method will need to exclude it,
    unless it is explicitly overridden in the child class.

    .. versionadded:: (cfdm) 1.8.7.0

    .. seealso:: `_docstring_special_substitutions`,
                 `_docstring_substitutions`,
                 `_docstring_package_depth`,
                 `__docstring_substitutions__`,
                 `__docstring_package_depth__`,
                 `__docstring_method_exclusions__`

    :Parameters:

        cls: class
            The class.

    :Returns:

        `set`
            The names of the methods to exclude from the docstring
            substutition process.

        '''
        out = [
            '_docstring_special_substitutions',
            '_docstring_package_depth',
        ]

        for klass in cls.__bases__[::-1]:
            d_s = getattr(klass, '_docstring_method_exclusions', None)
            if d_s is not None:
                out.extend(d_s(klass))
            else:
                d_s = getattr(klass, '__docstring_method_exclusions__', None)
                if d_s is not None:
                    out.extend(d_s(None))
        # --- End: for

        d_s = getattr(cls, '__docstring_method_exclusions__', None)
        if d_s is not None:
            out.extend(d_s(None))

        return set(out)

    @classmethod
    def _docstring_update(cls, package_name, class_name, f,
                          method_name, config):
        '''Perform docstring substitutions on a method at time of import.

    .. versionadded:: (cfdm) 1.8.7.0

        '''
        doc = f.__doc__
        if doc is None:
            return

        # ------------------------------------------------------------
        # Do general substitutions first
        # ------------------------------------------------------------
        for key, value in config.items():
            try:
                # Compiled regular expression substitution
                doc = key.sub(value, doc)
            except AttributeError:
                # String substitution
                doc = doc.replace(key, value)
        # --- End: for

        # ------------------------------------------------------------
        # Now do special substitutions
        # ------------------------------------------------------------
        # Insert the name of the package
        doc = doc.replace('{{package}}', package_name)

        # Insert the name of the class containing this method
        doc = doc.replace('{{class}}', class_name)

        # ----------------------------------------------------------------
        # Set the rewritten docstring on the method
        # ----------------------------------------------------------------
        f.__doc__ = doc

# --- End: class
