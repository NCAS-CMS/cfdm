from functools import wraps

from .functions import (
    LOG_LEVEL,
    _disable_logging,
    _reset_log_emergence_level,
)

from .constants import numeric_log_level_map


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


def _manage_log_level_via_verbosity(method_with_verbose_kwarg, calls=[0]):
    '''A decorator for managing log message filtering by verbosity argument.

    This enables overriding of the log severity level such that an integer
    input (lying in the valid range) to the decorated function will ignore
    the global cfdm.LOG_LEVEL() to configure a custom verbosity
    for the individual function call, applying to its logic and any
    functions it calls internally and lasting only the duration of the call.

    If verbose=None, as is the default, the LOG_LEVEL() determines
    which log messages are shown, as standard.

    Only use this to decorate functions which make log calls directly
    and have a 'verbose' keyword argument set to None by default.

    Note that the 'calls' keyword argument is to automatically track the number
    of decorated functions that are being (or about to be) executed, with the
    purpose of preventing resetting of the effective log level at the
    completion of decorated functions that are called inside other decorated
    functions (see comments in 'finally' statement for further explanation).
    Note (when it is of concern) that this approach may not be thread-safe.
    '''

    @wraps(method_with_verbose_kwarg)
    def verbose_override_wrapper(self, *args, **kwargs):
        # Increment indicates that one decorated function has started execution
        calls[0] += 1

        # Deliberately error if verbose kwarg not set, if not by user then
        # as a default to the decorated function, as this is crucial to usage.
        verbose = kwargs.get('verbose')

        # Convert Boolean cases for backwards compatibility. Need 'is' identity
        # rather than '==' (value) equivalency test, since 1 == True, etc.
        if verbose is True:
            verbose = 3  # max verbosity excluding debug levels
        elif verbose is False:
            verbose = 0  # corresponds to disabling logs i.e. no verbosity

        # Override log levels for the function & all it calls (to reset at end)
        if verbose in numeric_log_level_map.keys():
            _reset_log_emergence_level(numeric_log_level_map[verbose])
        elif verbose is not None:  # None as default, note exclude True & False
            # Print rather than log because if user specifies a verbose kwarg
            # they want to change the log levels so may have them disabled.
            print(
                "Invalid value for the 'verbose' keyword argument. Accepted "
                "values are integers from -1 to {} corresponding in the "
                "positive cases to increasing verbosity, or None, to "
                "configure the verbosity according to the global "
                "LOG_LEVEL setting.".format(
                    len(numeric_log_level_map) - 2)
            )
            return

        # First need to (temporarily) re-enable global logging if disabled
        # in the cases where you do not want to disable it anyway:
        if (LOG_LEVEL() == 'DISABLE' and verbose not in (0, None)):
            _disable_logging(at_level='NOTSET')  # enables all logging again

        # After method completes, re-set any changes to log level or enabling
        try:
            return method_with_verbose_kwarg(self, *args, **kwargs)
        except Exception:
            raise
        finally:  # so that crucial 'teardown' code runs even if method errors
            # Decrement indicates one decorated function has finished execution
            calls[0] -= 1
            # Due to the incrementing and decrementing of 'calls', it will
            # only be zero when the outermost decorated method has finished,
            # so the following condition prevents resetting occurring once
            # inner functions complete (which would mean any subsequent code
            # in the outer function would undesirably regain the global level):
            if calls[0] == 0:
                if verbose == 0:
                    _disable_logging(at_level='NOTSET')  # lift deactivation
                elif verbose in numeric_log_level_map.keys():
                    _reset_log_emergence_level(LOG_LEVEL())
                if LOG_LEVEL() == 'DISABLE' and verbose != 0:
                    _disable_logging()  # disable again after re-enabling

    return verbose_override_wrapper
