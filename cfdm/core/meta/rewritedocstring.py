import inspect
import re


class RewriteDocstringMeta(type):
    '''Modify docstrings.

    To do this, we intercede before the class is created and modify
    the docstrings of its attributes.

    This will not affect inherited methods, however, so we also need
    to loop through the parent classes. We cannot simply modify the
    docstrings, because then the parent classes' methods will have the
    wrong docstring. Instead, we must actually copy the functions, and
    then modify the docstring.

    Special treatment is given to methods decorated with @property and
    @classmethod. (Should other decorations be considered?)

    Based on
    http://www.jesshamrick.com/2013/04/17/rewriting-python-docstrings-with-a-metaclass/

    .. versionadded:: (cfdm) 1.8.7

    '''
    # Define the "plus class" regular expression
    _plus_class_regex = re.compile('{{\+(\w.*?)}}')

    def __new__(cls, name, parents, attrs):
        '''TODO

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
                parent, '__docstring_substitution__', None)
            if parent_docstring_rewrite is not None:
                docstring_rewrite.update(parent_docstring_rewrite(None))
        # --- End: for

        class_docstring_rewrite = attrs.get('__docstring_substitution__', None)
        if class_docstring_rewrite is not None:
            docstring_rewrite.update(class_docstring_rewrite(None))

        for attr_name, attr in attrs.items():
            # Skip special methods
            if attr_name.startswith('__'):
                continue

            if name == 'Field':
                print ('  ', attr_name)
            # Skip methods without docstrings
            if not hasattr(attr, '__doc__'):
                continue

            # @property or normal method
            if hasattr(attr, '__call__') or hasattr(attr, 'fget'):
                # Update docstring
                RewriteDocstringMeta._docstring_update(name, attr,
                                                       attr_name,
                                                       attrs['__module__'],
                                                       docstring_rewrite)
                continue

            # classmethod
            if isinstance(attr, classmethod):
                f = getattr(attr, '__func__')

                # Copy the method
                attr = type(f)(f.__code__, f.__globals__,
                               f.__name__, f.__defaults__,
                               f.__closure__)

                # Update docstring
                RewriteDocstringMeta._docstring_update(name, attr,
                                                       attr_name,
                                                       attrs['__module__'],
                                                       docstring_rewrite)

                attrs[attr_name] = classmethod(attr)
        # --- End: for

        for parent in parents:
            if name == 'Field':
                print (parent.__name__)

            for attr_name in dir(parent):
                
                if name == 'Field' and  parent.__name__ == 'PropertiesData':
                    print (attr_name)
                # We already have this method
                if attr_name in attrs:
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

                class_method = False

                if name == 'Field' and  parent.__name__ == 'PropertiesData' and attr_name == '_equals_preprocess':
                    print ('    name', original_f.__name__, original_f)
                    print ('    dir', dir(original_f))
                    print ('    __wrapped__', original_f.__wrapped__.__name__, original_f.__wrapped__)

                if name == 'Field' and  parent.__name__ == 'PropertiesData' and attr_name == '_parse_axes':
                    print ('    dir', dir(original_f))


                xxx = None
                
                try:
                    if hasattr(original_f, 'fget'):
                        # The original function is a property, i.e. it has
                        # been decorated with @property. Copy it.
                        attr = type(original_f)(original_f.fget,
                                                original_f.fset,
                                                original_f.fdel)
                    else:
                        # Skip non-callables
                        if not hasattr(original_f, '__call__'):
                            continue
                        if name == 'Field' and  parent.__name__ == 'PropertiesData':
                            print ('    DOING', attr_name)
                        # Note if the method is a classmethod
                        if inspect.ismethod(original_f):
                            class_method = True
                            print ('IS CLASS METHOD')
                            
                        if name == 'Field' and  parent.__name__ == 'PropertiesData':
                            print ('    namne', original_f.__name__)

                        
                            
                        f = getattr(original_f, '__func__', original_f)
                        if name == 'Field' and  parent.__name__ == 'PropertiesData':
                            print ('    namne', f.__name__)
                            print (f is original_f)

                        # Copy the method
                        attr = type(f)(f.__code__, f.__globals__,
                                       f.__name__, f.__defaults__,
                                       f.__closure__)
                        
                        if name == 'Field' and  parent.__name__ == 'PropertiesData':
                            print ('    namne', attr.__name__)

                        
                        if name == 'Field' and  parent.__name__ == 'PropertiesData' and attr_name == '_equals_preprocess':
                            print ('    dir 2', dir(f))
                            print ('    dir 3', dir(attr))

                        if hasattr(f, '__wrapped__'):
#                            xxx = attr
#                            attr = f.__wrapped__
                            if name == 'Field' and  parent.__name__ == 'PropertiesData':
                                print ('WRAPPED: ', attr_name)
                            
                    # Update the docstring
                    RewriteDocstringMeta._docstring_update(name, attr,
                                                           attr_name,
                                                           attrs['__module__'],
                                                           docstring_rewrite)

#                    if 
                    
                    # Register a classmethod
                    if class_method:
                        attr = classmethod(attr)

                    # Put the modified method back into the parent
                    # class
                    attrs[attr_name] = attr

                except Exception as error:
                    raise Exception(error)
        # --- End: for

        # Create the class
        return super().__new__(cls, name, parents, attrs)

    @staticmethod
    def _docstring_update(class_name, f, method_name, module, config):
        '''TODO

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
                doc = key.sub(value, doc)
            except AttributeError:
                doc = doc.replace(key, value)
        # --- End: for

        # ------------------------------------------------------------
        # Now do special substitutions
        # ------------------------------------------------------------
        doc = doc.replace('{{package}}', package_name)
        doc = doc.replace('{{class}}', class_name)

        if '{{+' in doc:
            if core:
                func = RewriteDocstringMeta._docstring_replacement_core_class
            else:
                func = RewriteDocstringMeta._docstring_replacement_class

            doc = RewriteDocstringMeta._plus_class_regex.sub(func, doc)

        # ----------------------------------------------------------------
        # Set the rewritten docstring on the method
        # ----------------------------------------------------------------
        f.__doc__ = doc

    @staticmethod
    def _docstring_replacement_class(match):
        '''Return the first of the match groups.

        '''
        return match.group(1)

    @staticmethod
    def _docstring_replacement_core_class(match):
        '''Return the first of the match groups prefixed by 'core.'

        '''
        return 'core.' + match.group(1)

    # --- End: class
