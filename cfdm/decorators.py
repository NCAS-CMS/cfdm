from functools import partial, wraps

from .constants import ValidLogLevels
from .functions import (
    _disable_logging,
    _is_valid_log_level_int,
    _reset_log_emergence_level,
    log_level,
)

# Identifier for '_inplace_enabled' to use as a (temporary) attribute name
INPLACE_ENABLED_PLACEHOLDER = "_inplace_store"


def _inplace_enabled(operation_method=None, *, default=False):
    """A decorator enabling operations to be applied in-place.

    If the decorated method has keyword argument *inplace* being equal
    to True, the function will be performed on `self` and return None,
    otherwise it will operate on a copy of ``self`` and return the
    processed copy.

    Note that methods decorated with this should assign the core
    variable storing the relevant instance for use throughout the
    method to ``_inplace_enabled_define_and_cleanup(self)``.

    :Parameters:

        operation_method: method

        default: `bool`

    """

    def decorator(operation_method, default=False):
        @wraps(operation_method)
        def inplace_wrapper(self, *args, **kwargs):
            is_inplace = kwargs.get("inplace", default)
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

    if operation_method is None:
        return partial(decorator, default=default)

    return decorator


def _inplace_enabled_define_and_cleanup(instance):
    """Deletes attribute set by _inplace_enabled, returning its value.

    Designed as a convenience function for use at the start of methods
    decorated by _inplace_enabled; the core variable used throughout
    for the instance in the decorated method should first be assigned
    to this function with the class instance as the input. For
    example:

    d = _inplace_enabled_define_and_cleanup(self)

    should be set initially for a method operating inplace or
    otherwise (via inplace_enabled) on a data array, d.

    In doing so, the relevant construct variable can be defined
    appropriately and the internal attribute created for that purpose
    by inplace_enabled (which is no longer required) can be cleaned
    up, all in one line.

    """
    try:
        x = instance._custom.pop(INPLACE_ENABLED_PLACEHOLDER)
    except (AttributeError, KeyError):
        x = instance.INPLACE_ENABLED_PLACEHOLDER
        del instance.INPLACE_ENABLED_PLACEHOLDER

    return x


def _manage_log_level_via_verbosity(method_with_verbose_kwarg, calls=[0]):
    """A decorator to manage log filtering by verbosity argument.

    This enables overriding of the log severity level such that an
    integer input (lying in the valid range) to the decorated function
    will ignore the global cfdm.log_level() to configure a custom
    verbosity for the individual function call, applying to its logic
    and any functions it calls internally and lasting only the
    duration of the call.

    If verbose=None, as is the default, the log_level() determines
    which log messages are shown, as standard.

    Only use this to decorate functions which make log calls directly
    and have a 'verbose' keyword argument set to None by default.

    Note that the 'calls' keyword argument is to automatically track
    the number of decorated functions that are being (or about to be)
    executed, with the purpose of preventing resetting of the
    effective log level at the completion of decorated functions that
    are called inside other decorated functions (see comments in
    'finally' statement for further explanation).  Note (when it is of
    concern) that this approach may not be thread-safe.

    """
    # Note that 'self' can be included in '*args' for any function calls
    # below, such that this decorator will work for both methods and
    # functions that are not bound to classes.

    @wraps(method_with_verbose_kwarg)
    def verbose_override_wrapper(*args, **kwargs):
        # Increment indicates that one decorated function has started
        # execution
        calls[0] += 1

        # Deliberately error if verbose kwarg not set, if not by user
        # then as a default to the decorated function, as this is
        # crucial to usage.
        verbose = kwargs.get("verbose")

        possible_levels = ", ".join(
            [val.name + " = " + str(val.value) for val in ValidLogLevels]
        )
        invalid_arg_msg = (
            f"Invalid value '{verbose}' for the 'verbose' keyword argument. "
            "Accepted values are integers corresponding in positive "
            f"cases to increasing verbosity (namely {possible_levels}), or "
            "None, to configure the verbosity according to the global "
            "log_level setting."
        )
        # First convert valid string inputs to the enum-mapped int constant:
        if isinstance(verbose, str):
            uppercase_arg = verbose.upper()
            if hasattr(ValidLogLevels, uppercase_arg):
                verbose = getattr(ValidLogLevels, uppercase_arg).value
            else:
                raise ValueError(invalid_arg_msg)

        # Convert Boolean cases for backwards compatibility. Need 'is'
        # identity rather than '==' (value) equivalency test, since 1
        # == True, etc.
        if verbose is True:
            verbose = 3  # max verbosity excluding debug levels
        elif verbose is False:
            verbose = 0  # corresponds to disabling logs i.e. no verbosity

        # Override log levels for the function & all it calls (to
        # reset at end)
        if verbose is not None:  # None as default, note exclude True & False
            if _is_valid_log_level_int(verbose):
                _reset_log_emergence_level(verbose)
            else:
                raise ValueError(invalid_arg_msg)

        # First need to (temporarily) re-enable global logging if
        # disabled in the cases where you do not want to disable it
        # anyway:
        if log_level() == "DISABLE" and verbose not in (0, None):
            _disable_logging(at_level="NOTSET")  # enables all logging again

        # After method completes, re-set any changes to log level or
        # enabling
        try:
            return method_with_verbose_kwarg(*args, **kwargs)
        except Exception:
            raise
        finally:  # so that crucial 'teardown' code runs even if
            # method errors Decrement indicates one decorated function
            # has finished execution
            calls[0] -= 1
            # Due to the incrementing and decrementing of 'calls', it
            # will only be zero when the outermost decorated method
            # has finished, so the following condition prevents
            # resetting occurring once inner functions complete (which
            # would mean any subsequent code in the outer function
            # would undesirably regain the global level):
            if calls[0] == 0:
                if verbose == 0:
                    _disable_logging(at_level="NOTSET")  # lift deactivation
                elif verbose is not None and _is_valid_log_level_int(verbose):
                    _reset_log_emergence_level(log_level())
                if log_level() == "DISABLE" and verbose != 0:
                    _disable_logging()  # disable again after re-enabling

    return verbose_override_wrapper


# @_test_decorator_args('i') -> example usage for decorating, using i kwarg
def _test_decorator_args(*dec_args):
    """A wrapper to provide positional arguments to the decorator."""

    def deprecated_kwarg_check_decorator(operation_method):
        """A decorator for a deprecation check on given kwargs.

        To specify deprecated kwargs, supply them as string arguments, e.g:

            @_test_decorator_args('i')
            @_test_decorator_args('i', 'traceback')

        For a specified list `*dec_args`, check if the decorated
        method has been supplied with any of the elements as keyword
        arguments and if so, call _DEPRECATION_ERROR_KWARGS on them,
        optionally providing a custom message to raise inside it.

        """

        @wraps(operation_method)
        def precede_with_kwarg_deprecation_check(self, *args, **kwargs):
            print(
                "In precede_with_kwarg_deprecation_check. dec_args=", dec_args
            )

            # Decorated method has same return signature as if undecorated:
            return

        return precede_with_kwarg_deprecation_check

    return deprecated_kwarg_check_decorator


def _display_or_return(method_with_display_kwarg):
    """A decorator enabling a string to be printed rather than returned.

    If the decorated method has keyword argument *display* being equal
    to True, by default or from being set as such, the function will
    print the output that would otherwise be returned and return `None`.

    :Parameters:

        method_with_display_kwarg: method

    """

    @wraps(method_with_display_kwarg)
    def end_with_display_or_return_logic(self, *args, **kwargs):
        string = method_with_display_kwarg(self, *args, **kwargs)

        # display=True is always default, so if display not provided, set True
        display = kwargs.get("display", True)

        if display:
            print(string)
        else:
            return string

    return end_with_display_or_return_logic
