import functools
import inspect


def _docstring_update(class_name, f, method_name, module, config):
    '''
    
    '''
    doc = f.__doc__
    if doc is None:
        return
    
    core = False
    module = module.split('.')
    if len(module) >= 2:
        package_name, package2 = module[:2]
        if package_name == 'cfdm' and package2 == 'core':
            class_name = 'core.' + class_name
            core = True
    else:
        package_name = module[0]

    # ----------------------------------------------------------------
    # Do special substitutions first
    # ----------------------------------------------------------------
    config = config.copy()

    key = '{{package}}'
    if config.pop(key, None):
        doc = doc.replace(key, package_name)
    
    key = '{{class}}'
    if config.pop(key, None):
        doc = doc.replace(key, class_name)
    
    key = '{{+class}}'
    value = config.pop(key, None)
    if value is not None:
        regex, func = value
        class_func = functools.partial(func, core=core)
        doc = regex.sub(class_func, doc)
        
    # ----------------------------------------------------------------
    # Process keyword parameter descriptions
    # ----------------------------------------------------------------
    for key, value in config.copy().items():
        if ':' not in key:
            continue

        value = value.replace('{{package}}', package_name)
        value = value.replace('{{class}}', class_name)
        if '{{+' in value:
            value = regex.sub(class_func, value)

        doc = doc.replace(key, value)
        
        del config[key]
            
    # ----------------------------------------------------------------
    # Process everything else
    # ----------------------------------------------------------------
    for key, value in config.items():
        if key.startswith('{{<'):
            regex, func = value
            doc = regex.sub(func, doc)
        else:        
            doc = doc.replace(key, value)
    # --- End: for

    # ----------------------------------------------------------------
    # Add the rewritten docstring to the method
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

    Special treatment is given to methods decorated with @property and
    @classmethod. (Should other decorations be considered?)

    Based on
    http://www.jesshamrick.com/2013/04/17/rewriting-python-docstrings-with-a-metaclass/

    .. versionadded:: 1.8.7

    '''
    def __new__(cls, name, parents, attrs):
        docstring_rewrite = attrs.get('__docstring_substitution__', None)
        if docstring_rewrite is not None:
            docstring_rewrite = docstring_rewrite(cls)
        else:
            docstring_rewrite = {}

        for attr_name in attrs:
            # Skip special and private methods
            if attr_name.startswith('_'):
                continue
    
            # Skip non-functions
            attr = attrs[attr_name]
                
            if not hasattr(attr, '__doc__'):
                continue

            # @property or normal method
            if hasattr(attr, '__call__') or hasattr(attr, 'fget'):
                # Update docstring
                if docstring_rewrite:
                    _docstring_update(name, attr, attr_name,
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
                if docstring_rewrite:
                    _docstring_update(name, attr, attr_name,
                                      attrs['__module__'],
                                      docstring_rewrite)

                attrs[attr_name] = classmethod(attr)
        # --- End: for
 
        for parent in parents:
            docstring_rewrite = getattr(
                parent, '__docstring_substitution__', None)
            if docstring_rewrite is not None:
                docstring_rewrite = docstring_rewrite(parent)
            else:
                docstring_rewrite = {}

            if not docstring_rewrite:
                # Docstring rewriting has been disabled for this class
                continue
            
            for attr_name in dir(parent):
                # We already have this method
                if attr_name in attrs:
                    continue
 
                # Skip special and private methods
                if attr_name.startswith('_'):
                    continue

                # ----------------------------------------------------
                # Get the original method, copy it, update the
                # docstring, and put the mosfied copy back into the
                # parent class.
                # ----------------------------------------------------
                original_f = getattr(parent, attr_name)

                class_method = False

                try:
                    if hasattr(original_f , 'fget'):
                        # The original function is a property, i.e. it has
                        # been decorated with @property. Copy it.
                        attr = type(original_f)(original_f.fget,
                                                original_f.fset,
                                                original_f.fdel)
                    else:
                        # Skip non-callables
                        if not hasattr(original_f, '__call__'):
                            continue

                        # Note if the method is a classmethod
                        if inspect.ismethod(original_f):
                            class_method = True
                            
                        f = getattr(original_f, '__func__', original_f)
    
                        # Copy the method
                        attr = type(f)(f.__code__, f.__globals__,
                                       f.__name__, f.__defaults__,
                                       f.__closure__)

                    # Update the docstring
                    if docstring_rewrite:
                        _docstring_update(name, attr, attr_name,
                                          attrs['__module__'],
                                          docstring_rewrite)
                    
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

#--- End: class
