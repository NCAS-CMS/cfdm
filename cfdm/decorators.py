from functools import wraps

from .functions import (
    LOG_SEVERITY_LEVEL,
    _disable_logging,
    _reset_log_severity_level,
)


# Identifier for 'inplace_enabled' to use as internal '_custom' dictionary key,
# or directly as a (temporary) attribute name if '_custom' is not provided:
INPLACE_ENABLED_PLACEHOLDER = '_to_assign'


def _inplace_enabled(operation_method):
    '''A decorator enabling operations to be applied in-place.

    If the decorated method has keyword argument `inplace` being equal to
    True, the function will be performed on `self` and return None, otherwise
    it will operate on a copy of `self` & return the processed copy.

    Note that methods decorated with this should assign the core variable
    storing the relevant instance for use throughout the method to
    `_inplace_enabled_define_and_cleanup(self)`.

    '''
    @wraps(operation_method)
    def inplace_wrapper(self, *args, **kwargs):
        is_inplace = kwargs.get('inplace')
        try:
            if is_inplace:
                # create an attribute equal to 'self'
                self._custom[INPLACE_ENABLED_PLACEHOLDER] = self
            else:
                # create an attribute equal to a (shallow) copy of 'self'
                self._custom[INPLACE_ENABLED_PLACEHOLDER] = self.copy()
        # '_custom' not available for object so have to use a direct attribute
        # for the storage, which is not as desirable since it is more exposed:
        except AttributeError:
            if is_inplace:
                self.INPLACE_ENABLED_PLACEHOLDER = self
            else:
                self.INPLACE_ENABLED_PLACEHOLDER = self.copy()

        processed_copy = operation_method(self, *args, **kwargs)

        if is_inplace:
            return  # decorated function returns None in this case
        else:
            return processed_copy

    return inplace_wrapper


def _inplace_enabled_define_and_cleanup(instance):
    '''Delete attribute set by inable_enabled but store and return its value.

    Designed as a convenience function for use at the start of methods
    decorated by inplace_enabled; the core variable used throughout for the
    instance in the decorated method should first be assigned to this
    function with the class instance as the input. For example:

    d = _inplace_enabled_define_and_cleanup(self)

    should be set initially for a method operating inplace or otherwise
    (via inplace_enabled) on a data array, d.

    In doing so, the relevant construct variable can be defined appropriately
    and the internal attribute created for that purpose by inplace_enabled
    (which is no longer required) can be cleaned up, all in one line.

    '''
    try:
        x = instance._custom.pop(INPLACE_ENABLED_PLACEHOLDER)
    except (AttributeError, KeyError):
        x = instance.INPLACE_ENABLED_PLACEHOLDER
        del instance.INPLACE_ENABLED_PLACEHOLDER

    return x


def _manage_log_level_via_verbosity(method_with_verbose_kwarg):
    '''A decorator for managing log message filtering by verbosity argument.

    This enables overriding of the log severity level such that a verbose=True
    input to the decorated method will force all log messages called within
    the method (only) to be displayed, even if less than the
    cfdm.LOG_SEVERITY_LEVEL() which would otherwise filter them out, and
    verbose=False input will disable all log messages appearing, again
    regardless of LOG_SEVERITY_LEVEL(). If verbose=None, as is the default,
    the LOG_SEVERITY_LEVEL() determines which log messages are shown, as
    standard.

    Only use this to decorate functions which make log calls directly
    and have a 'verbose' keyword argument set to None by default.
    '''

    @wraps(method_with_verbose_kwarg)
    def verbose_override_wrapper(self, *args, **kwargs):
        verbose = kwargs.get('verbose')

        if verbose:
            # This level is effectively below 'DEBUG' and results in all log
            # messages being returned, no matter their level. Note this only
            # holds over the time of method execution (see reversion below).
            _reset_log_severity_level('NOTSET')
        elif verbose is False:  # deliberatly excluding verbose=None case
            _disable_logging()  # prevents any log messages being displayed

        try:
            return method_with_verbose_kwarg(self, *args, **kwargs)
        except Exception as exc:
            raise
        finally:  # so above changes are reverted even when method errors
            if verbose:
                _reset_log_severity_level(LOG_SEVERITY_LEVEL())  # revert
            elif verbose is False:  # deliberatly excluding verbose=None case
                _disable_logging('NOTSET')  # lift the deactivation (re-enable)

    return verbose_override_wrapper
