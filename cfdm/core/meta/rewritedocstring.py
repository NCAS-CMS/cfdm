import inspect
import re


# Define the "plus class" regular expression.
#
# E.g. matches: {{+Data}} with Data as the grouped match
_plus_class_regex = re.compile('{{\+(\w.*?)}}')


def _docstring_replacement_class(match):
    '''Return the first of the match groups.

    .. versionadded:: (cfdm) 1.8.7.0

        '''
    return match.group(1)


def _docstring_replacement_core_class(match):
    '''Return the first of the match groups prefixed by 'core.'

    .. versionadded:: (cfdm) 1.8.7.0

        '''
    return 'core.' + match.group(1)


def _docstring_update(class_name, f, method_name, module, config):
    '''TODO

    .. versionadded:: (cfdm) 1.8.7.0

    '''
    doc = f.__doc__
    if doc is None:
        return

    # ------------------------------------------------------------
    # Find the package name, class name, and whether or we are in
    # the cfdm.core package.
    # ------------------------------------------------------------
    core = False
    module = module.split('.')
    if len(module) >= 2:
        package_name, package2 = module[:2]
        if package_name == 'cfdm' and package2 == 'core':
            class_name = 'core.' + class_name
            core = True
    else:
        package_name = module[0]

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

    # Insert the name of a different class
    if '{{+' in doc:
        if core:
            func = _docstring_replacement_core_class
        else:
            func = _docstring_replacement_class

        doc = _plus_class_regex.sub(func, doc)

    # ----------------------------------------------------------------
    # Set the rewritten docstring on the method
    # ----------------------------------------------------------------
    f.__doc__ = doc


class RewriteDocstringMeta(type):
    '''Modify docstrings.

    To do this, we intercede before the class is created and modify
    the docstrings of its attributes.

    This will not affect inherited methods, however, so we also need
    to loop through the parent classes. We cannot simply modify the
    docstrings, because then the parent classes' methods will have the
    wrong docstring. Instead, we must actually copy the functions, and
    then modify the docstring.

    Special treatment is given to methods decorated with @property,
    @staticmethod and @classmethod, as well as user-defined
    decorations.

    Based on
    http://www.jesshamrick.com/2013/04/17/rewriting-python-docstrings-with-a-metaclass/

    .. versionadded:: (cfdm) 1.8.7.0

    '''
    def __new__(cls, class_name, parents, attrs):
        '''TODO

    .. versionadded:: (cfdm) 1.8.7.0

        '''
        # ------------------------------------------------------------
        # Combine the docstring substitutions from all classes in the
        # inheritance tree.
        #
        # The value for a key that occurs in multiple classes will be
        # taken from the class closest to the child class.
        # ------------------------------------------------------------
        docstring_rewrite = {}
        for parent in parents[::-1]:
            parent_docstring_rewrite = getattr(
                parent, '_docstring_substitution', None)
            if parent_docstring_rewrite is not None:
                docstring_rewrite.update(parent_docstring_rewrite())
            else:
                parent_docstring_rewrite = getattr(
                    parent, '__docstring_substitution__', None)
                if parent_docstring_rewrite is not None:
                    docstring_rewrite.update(parent_docstring_rewrite(None))
        # --- End: for

        class_docstring_rewrite = attrs.get('__docstring_substitution__', None)
        if class_docstring_rewrite is not None:
            docstring_rewrite.update(class_docstring_rewrite(None))

        for key in docstring_rewrite:
            if key in ('{{class}}', '{{package}}') or key.startswith('{{+'):
                raise ValueError(
                    "Can't use {!r} as a user-defined "
                    "docstring substitution.".format(key)
                )
        # --- End: for

        module = attrs['__module__']

        for attr_name, attr in attrs.items():
            # Skip special methods
            if attr_name.startswith('__'):
                continue

            # Skip methods without docstrings
            if not hasattr(attr, '__doc__'):
                continue

            # @property
            if hasattr(attr, 'fget'):
                # Note that here inspect.isroutine(attr) is False for
                # @property methods (but this is not the case for
                # properties in the parent classes).
                _docstring_update(class_name, attr, attr_name, module,
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

            # Update docstring
            _docstring_update(class_name, attr, attr_name, module,
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

        for parent in parents:
            for attr_name in dir(parent):

                if attr_name in attrs:
                    # We already have this method from higher up in
                    # the method resolution order, so do not overwrite
                    # it and move on to to the next method.
                    continue

                # Skip special methods
                if attr_name.startswith('__'):
                    continue

                # ----------------------------------------------------
                # Get the original method, copy it, update the
                # docstring, and put the mosfied copy back into the
                # parent class.
                # ----------------------------------------------------
                original_f = getattr(parent, attr_name)

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

                        if is_wrapped:
                            attr.__doc__ = original_f.__doc__
                    # --- End: if

                    # Update the docstring
                    _docstring_update(class_name, attr, attr_name,
                                      module, docstring_rewrite)

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
                    raise RuntimeError(str(error) +
                                       ' '.join([':',
                                                 parent.__name__,
                                                 attr_name]))
        # --- End: for

        # Create the class
        return super().__new__(cls, class_name, parents, attrs)

    @classmethod
    def _special_docstring_substitutions(cls):
        '''Return the special docstring subtitutions.
        
    ``{{class}}`` is replaced by the name of the class.

    ``{{package}}`` is replaced by the name of the module, i.e.
    ``'.'.split({{class}}.__module__)[0]``
  
    ``re.compile('{{\+(\w.*?)}}')`` is replaced the name of the class
    named by the pattern's group.

    :Returns:

        `tuple`
            The special docstring substitutions.

        '''
        return (
            '{{class}}',
            '{{package}}',
            _plus_class_regex,
        )
    
    # --- End: class
