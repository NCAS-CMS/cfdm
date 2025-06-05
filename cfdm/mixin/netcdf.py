from numbers import Integral
from re import split

from dask.utils import parse_bytes

from ..core.functions import deepcopy
from ..functions import _DEPRECATION_ERROR_METHOD


class DeprecationError(Exception):
    """An error indicating a method is no longer available."""

    pass


class NetCDFMixin:
    """Mixin class for accessing netCDF entities.

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __initialise_from_source(self, source, copy=True):
        """Initialise netCDF components from a source.

        This method is called by
        `_Container__parent_initialise_from_source`, which in turn is
        called by `cfdm.core.Container.__init__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            source:
                The object from which to extract the initialisation
                information. Typically, but not necessarily, a
                `{{class}}` object.

            copy: `bool`, optional
                If True (the default) then deep copy the
                initialisation information.

        :Returns:

            `None`

        """
        try:
            n = source._get_component("netcdf", None)
        except AttributeError:
            pass
        else:
            if n is not None:
                self._set_component("netcdf", n, copy=copy)

    def _get_netcdf(self):
        """Get the ``netcdf`` component dictionary.

        If the dictionary does not exist then an empty dictionary is
        automatically created and stored.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `_set_netcdf`

        :Returns:

            `dict`

        """
        netcdf = self._get_component("netcdf", None)
        if netcdf is None:
            netcdf = {}
            self._set_component("netcdf", netcdf, copy=False)

        return netcdf

    def _nc_del(self, entity, default=ValueError()):
        """Remove the netCDF entity name.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_nc_get`, `_nc_has`, `_nc_set`

        :Parameters:

            entity: `str`
                The name of the netCDF entity.

                *Parameter example:*
                  ``'subsampled_dimension'``

            default: optional
                Return the value of the *default* parameter if the
                netCDF entity has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The removed netCDF entity.

        **Examples**

        >>> f._nc_set('variable', 'time')
        >>> f._nc_has('variable')()
        True
        >>> f._nc_get('variable')()
        'time'
        >>> f._nc_del('variable')()
        'time'
        >>> f._nc_has('variable')()
        False
        >>> print(f._nc_get('variable', None))
        None
        >>> print(f._nc_del('variable', None))
        None

        """
        try:
            return self._get_netcdf().pop(entity)
        except KeyError:
            if default is None:
                return default

            entity = entity.replace("_", " ")
            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF {entity} name",
            )

    def _nc_get(self, entity, default=ValueError()):
        """Return the netCDF entity name.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_nc_del`, `_nc_has`, `_nc_set`

        :Parameters:

            entity: `str`
                The name of the netCDF entity.

                *Parameter example:*
                  ``'subsampled_dimension'``

            default: optional
                Return the value of the *default* parameter if the
                netCDF entity name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The netCDF entity name.

        **Examples**

        >>> f._nc_set('variable', 'time')
        >>> f._nc_has('variable')()
        True
        >>> f._nc_get('variable')()
        'time'
        >>> f._nc_del('variable')()
        'time'
        >>> f._nc_has('variable')()
        False
        >>> print(f._nc_get('variable', None))
        None
        >>> print(f._nc_del('variable', None))
        None

        """
        try:
            return self._get_netcdf()[entity]
        except KeyError:
            if default is None:
                return default

            entity = entity.replace("_", " ")
            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF {entity} name",
            )

    def _nc_has(self, entity):
        """Whether the netCDF entity name has been set.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_nc_del`, `_nc_get`, `_nc_set`

        :Parameters:

            entity: `str`
                The name of the netCDF entity.

                *Parameter example:*
                  ``'subsampled_dimension'``

        :Returns:

            `bool`
                `True` if the netCDF entity name has been set,
                otherwise `False`.

        **Examples**

        >>> f._nc_set('variable', 'time')
        >>> f._nc_has('variable')()
        True
        >>> f._nc_get('variable')()
        'time'
        >>> f._nc_del('variable')()
        'time'
        >>> f._nc_has('variable')()
        False
        >>> print(f._nc_get('variable', None))
        None
        >>> print(f._nc_del('variable', None))
        None

        """
        return entity in self._get_netcdf()

    def _nc_set(self, entity, value):
        """Set the netCDF entity name.

        If there are any ``/`` (slash) characters in the netCDF entity
        name then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_nc_del`, `_nc_get`, `_nc_has`

        :Parameters:

            entity: `str`
                The name of the netCDF entity.

                *Parameter example:*
                  ``'subsampled_dimension'``

            value: `str`
                The value for the netCDF entity name.

        :Returns:

            `None`

        **Examples**

        >>> f._nc_set('variable', 'time')
        >>> f._nc_has('variable')()
        True
        >>> f._nc_get('variable')()
        'time'
        >>> f._nc_del('variable')()
        'time'
        >>> f._nc_has('variable')()
        False
        >>> print(f._nc_get('variable', None))
        None
        >>> print(f._nc_del('variable', None))
        None

        """
        if not value or value == "/":
            raise ValueError(f"Invalid netCDF {entity} name: {value!r}")

        if "/" in value:
            if not value.startswith("/"):
                entity = entity.replace("_", " ")
                raise ValueError(
                    f"A netCDF {entity} name with a group "
                    f"structure must start with a '/'. Got {value!r}"
                )

            if value.count("/") == 1:
                value = value[1:]
            elif value.endswith("/"):
                entity = entity.replace("_", " ")
                raise ValueError(
                    f"A netCDF {entity} name with a "
                    f"group structure can't end with a '/'. Got {value!r}"
                )

        self._set_netcdf(entity, value)

    def _set_netcdf(self, key, value):
        """Set a new key in the ``netcdf`` component dictionary.

        If the component does not exist then it is automatically
        created.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `_get_netcdf`

        :Parameters:

            key:
                The dictionary key.

            value:
                The dictionary value.

        :Returns:

            `None`

        """
        netcdf = self._get_netcdf()
        netcdf[key] = value


class NetCDFGroupsMixin:
    """Mixin class for accessing netCDF(4) hierarchical groups.

    .. versionadded:: (cfdm) 1.8.6

    """

    @classmethod
    def _nc_groups(cls, nc_get):
        """Return the netCDF group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `_nc_clear_groups`, `_nc_set_groups`

        :Parameters:

            nc_get: function
                The method which gets the netCDF name.

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        See the examples in classes which inherit this method.

        """
        name = nc_get(default="")
        return tuple(name.split("/")[1:-1])

    @classmethod
    def _nc_set_groups(cls, groups, nc_get, nc_set, nc_groups):
        """Set the netCDF group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `_nc_clear_groups`, `_nc_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

            nc_get: function
                The method which gets the netCDF name.

            nc_set: function
                The method which sets the netCDF name.

            nc_groups: function
                The method which returns existing group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        See the examples in classes which inherit this method.

        """
        old = nc_groups()

        name = nc_get(default="")
        name = name.split("/")[-1]
        if not name:
            raise ValueError("Can't set groups when there is no netCDF name")

        if groups:
            for group in groups:
                if "/" in group:
                    raise ValueError(
                        f"Can't have '/' character in group name: {group!r}"
                    )

            name = "/".join(("",) + tuple(groups) + (name,))

        if name:
            nc_set(name)

        return old

    @classmethod
    def _nc_clear_groups(cls, nc_get, nc_set, nc_groups):
        """Remove the netCDF group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `_nc_groups`, `_nc_set_groups`

        :Parameters:

            nc_get: function
                The method which gets the netCDF name.

            nc_set: function
                The method which sets the netCDF name.

            nc_groups: function
                The method which returns existing group structure.

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        See the examples in classes which inherit this method.

        """
        old = nc_groups()

        name = nc_get(default="")
        name = name.split("/")[-1]
        if name:
            nc_set(name)

        return old


class NetCDFDimension(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin class for accessing the netCDF dimension name.

    .. versionadded:: (cfdm) 1.7.0

    """

    def nc_del_dimension(self, default=ValueError()):
        """Remove the netCDF dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_get_dimension`, `nc_has_dimension`,
                     `nc_set_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF dimension name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The removed netCDF dimension name.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_has_dimension()
        True
        >>> f.nc_get_dimension()
        'time'
        >>> f.nc_del_dimension()
        'time'
        >>> f.nc_has_dimension()
        False
        >>> print(f.nc_get_dimension(None))
        None
        >>> print(f.nc_del_dimension(None))
        None

        """
        return self._nc_del("dimension", default=default)

    def nc_get_dimension(self, default=ValueError()):
        """Return the netCDF dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_dimension`, `nc_has_dimension`,
                     `nc_set_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF dimension name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The netCDF dimension name.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_has_dimension()
        True
        >>> f.nc_get_dimension()
        'time'
        >>> f.nc_del_dimension()
        'time'
        >>> f.nc_has_dimension()
        False
        >>> print(f.nc_get_dimension(None))
        None
        >>> print(f.nc_del_dimension(None))
        None

        """
        return self._nc_get("dimension", default=default)

    def nc_has_dimension(self):
        """Whether the netCDF dimension name has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_dimension`, `nc_get_dimension`,
                     `nc_set_dimension`

        :Returns:

            `bool`
                `True` if the netCDF dimension name has been set,
                otherwise `False`.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_has_dimension()
        True
        >>> f.nc_get_dimension()
        'time'
        >>> f.nc_del_dimension()
        'time'
        >>> f.nc_has_dimension()
        False
        >>> print(f.nc_get_dimension(None))
        None
        >>> print(f.nc_del_dimension(None))
        None

        """
        return self._nc_has("dimension")

    def nc_set_dimension(self, value):
        """Set the netCDF dimension name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_dimension`, `nc_get_dimension`,
                     `nc_has_dimension`

        :Parameters:

            value: `str`
                The value for the netCDF dimension name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_has_dimension()
        True
        >>> f.nc_get_dimension()
        'time'
        >>> f.nc_del_dimension()
        'time'
        >>> f.nc_has_dimension()
        False
        >>> print(f.nc_get_dimension(None))
        None
        >>> print(f.nc_del_dimension(None))
        None

        """
        return self._nc_set("dimension", value)

    def nc_dimension_groups(self):
        """Return the netCDF dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_dimension_groups`,
                     `nc_set_dimension_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_dimension_groups()
        ()
        >>> f.nc_set_dimension_groups(['forecast', 'model'])
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        '/forecast/model/time'
        >>> f.nc_clear_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        'time'

        >>> f.nc_set_dimension('/forecast/model/time')
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_dimension('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_dimension_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_dimension)

    def nc_set_dimension_groups(self, groups):
        """Set the netCDF dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for setting the group structure is to
        set the netCDF dimension name, with `nc_set_dimension`, with
        the group structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_dimension_groups`, `nc_dimension_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_dimension_groups()
        ()
        >>> f.nc_set_dimension_groups(['forecast', 'model'])
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        '/forecast/model/time'
        >>> f.nc_clear_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        'time'

        >>> f.nc_set_dimension('/forecast/model/time')
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_dimension('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_dimension_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_dimension,
            nc_set=self.nc_set_dimension,
            nc_groups=self.nc_dimension_groups,
        )

    def nc_clear_dimension_groups(self):
        """Remove the netCDF dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for removing the group structure is
        to set the netCDF dimension name, with `nc_set_dimension`,
        with no ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_dimension_groups`, `nc_set_dimension_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_dimension('time')
        >>> f.nc_dimension_groups()
        ()
        >>> f.nc_set_dimension_groups(['forecast', 'model'])
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        '/forecast/model/time'
        >>> f.nc_clear_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_dimension()
        'time'

        >>> f.nc_set_dimension('/forecast/model/time')
        >>> f.nc_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_dimension('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_dimension_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_dimension,
            nc_set=self.nc_set_dimension,
            nc_groups=self.nc_dimension_groups,
        )


class NetCDFVariable(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin class for accessing the netCDF variable name.

    .. versionadded:: (cfdm) 1.7.0

    """

    def nc_del_variable(self, default=ValueError()):
        """Remove the netCDF variable name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_get_variable`, `nc_has_variable`,
                     `nc_set_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF variable name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The removed netCDF variable name.

        **Examples**

        >>> f.nc_set_variable('tas')
        >>> f.nc_has_variable()
        True
        >>> f.nc_get_variable()
        'tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.nc_has_variable()
        False
        >>> print(f.nc_get_variable(None))
        None
        >>> print(f.nc_del_variable(None))
        None

        """
        return self._nc_del("variable", default=default)

    def nc_get_variable(self, default=ValueError()):
        """Return the netCDF variable name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_variable`, `nc_has_variable`,
                     `nc_set_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF variable name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The netCDF variable name. If unset then *default* is
                returned, if provided.

        **Examples**

        >>> f.nc_set_variable('tas')
        >>> f.nc_has_variable()
        True
        >>> f.nc_get_variable()
        'tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.nc_has_variable()
        False
        >>> print(f.nc_get_variable(None))
        None
        >>> print(f.nc_del_variable(None))
        None

        """
        return self._nc_get("variable", default=default)

    def nc_has_variable(self):
        """Whether the netCDF variable name has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_variable`, `nc_get_variable`,
                     `nc_set_variable`

        :Returns:

            `bool`
                `True` if the netCDF variable name has been set, otherwise
                `False`.

        **Examples**

        >>> f.nc_set_variable('tas')
        >>> f.nc_has_variable()
        True
        >>> f.nc_get_variable()
        'tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.nc_has_variable()
        False
        >>> print(f.nc_get_variable(None))
        None
        >>> print(f.nc_del_variable(None))
        None

        """
        return "variable" in self._get_netcdf()

    def nc_set_variable(self, value):
        """Set the netCDF variable name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_variable`, `nc_get_variable`,
                     `nc_has_variable`

        :Parameters:

            value: `str`
                The value for the netCDF variable name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_variable('tas')
        >>> f.nc_has_variable()
        True
        >>> f.nc_get_variable()
        'tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.nc_has_variable()
        False
        >>> print(f.nc_get_variable(None))
        None
        >>> print(f.nc_del_variable(None))
        None

        """
        return self._nc_set("variable", value)

    def nc_variable_groups(self):
        """Return the netCDF variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_variable_groups`,
                     `nc_set_variable_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_variable('time')
        >>> f.nc_variable_groups()
        ()
        >>> f.nc_set_variable_groups(['forecast', 'model'])
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        '/forecast/model/time'
        >>> f.nc_clear_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_variable_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_variable)

    def nc_set_variable_groups(self, groups):
        """Set the netCDF variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for setting the group structure is to
        set the netCDF variable name, with `nc_set_variable`, with the
        group structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_variable_groups`, `nc_variable_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_variable('time')
        >>> f.nc_variable_groups()
        ()
        >>> f.nc_set_variable_groups(['forecast', 'model'])
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        '/forecast/model/time'
        >>> f.nc_clear_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_variable_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_variable,
            nc_set=self.nc_set_variable,
            nc_groups=self.nc_variable_groups,
        )

    def nc_clear_variable_groups(self):
        """Remove the netCDF variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for removing the group structure is
        to set the netCDF variable name, with `nc_set_variable`, with
        no ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_variable_groups`, `nc_set_variable_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_variable('time')
        >>> f.nc_variable_groups()
        ()
        >>> f.nc_set_variable_groups(['forecast', 'model'])
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        '/forecast/model/time'
        >>> f.nc_clear_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_variable_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_variable,
            nc_set=self.nc_set_variable,
            nc_groups=self.nc_variable_groups,
        )


class NetCDFSampleDimension(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin class for accessing the netCDF sample dimension name.

    .. versionadded:: (cfdm) 1.7.0

    """

    def nc_del_sample_dimension(self, default=ValueError()):
        """Remove the netCDF sample dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_get_sample_dimension`,
                     `nc_has_sample_dimension`,
                     `nc_set_sample_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF sample dimension name has not been set. If set
                to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The removed netCDF sample dimension name.

        **Examples**

        >>> f.nc_set_sample_dimension('time')
        >>> f.nc_has_sample_dimension()
        True
        >>> f.nc_get_sample_dimension()
        'time'
        >>> f.nc_del_sample_dimension()
        'time'
        >>> f.nc_has_sample_dimension()
        False
        >>> print(f.nc_get_sample_dimension(None))
        None
        >>> print(f.nc_del_sample_dimension(None))
        None

        """
        try:
            return self._get_netcdf().pop("sample_dimension")
        except KeyError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF sample dimension name",
            )

    def nc_get_sample_dimension(self, default=ValueError()):
        """Return the netCDF sample dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_sample_dimension`, `nc_has_sample_dimension`,
                     `nc_set_sample_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF sample dimension name has not been set. If set
                to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The netCDF sample dimension name.

        **Examples**

        >>> f.nc_set_sample_dimension('time')
        >>> f.nc_has_sample_dimension()
        True
        >>> f.nc_get_sample_dimension()
        'time'
        >>> f.nc_del_sample_dimension()
        'time'
        >>> f.nc_has_sample_dimension()
        False
        >>> print(f.nc_get_sample_dimension(None))
        None
        >>> print(f.nc_del_sample_dimension(None))
        None

        """
        try:
            return self._get_netcdf()["sample_dimension"]
        except KeyError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF sample dimension name",
            )

    def nc_has_sample_dimension(self):
        """Whether the netCDF sample dimension name has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_sample_dimension`, `nc_get_sample_dimension`,
                     `nc_set_sample_dimension`

        :Returns:

            `bool`
                `True` if the netCDF sample dimension name has been set,
                otherwise `False`.

        **Examples**

        >>> f.nc_set_sample_dimension('time')
        >>> f.nc_has_sample_dimension()
        True
        >>> f.nc_get_sample_dimension()
        'time'
        >>> f.nc_del_sample_dimension()
        'time'
        >>> f.nc_has_sample_dimension()
        False
        >>> print(f.nc_get_sample_dimension(None))
        None
        >>> print(f.nc_del_sample_dimension(None))
        None

        """
        return "sample_dimension" in self._get_netcdf()

    def nc_set_sample_dimension(self, value):
        """Set the netCDF sample dimension name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_del_sample_dimension`, `nc_get_sample_dimension`,
                     `nc_has_sample_dimension`

        :Parameters:

            value: `str`
                The value for the netCDF sample dimension name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_sample_dimension('time')
        >>> f.nc_has_sample_dimension()
        True
        >>> f.nc_get_sample_dimension()
        'time'
        >>> f.nc_del_sample_dimension()
        'time'
        >>> f.nc_has_sample_dimension()
        False
        >>> print(f.nc_get_sample_dimension(None))
        None
        >>> print(f.nc_del_sample_dimension(None))
        None

        """
        if not value or value == "/":
            raise ValueError(
                f"Invalid netCDF sample dimension name: {value!r}"
            )

        if "/" in value:
            if not value.startswith("/"):
                raise ValueError(
                    "A netCDF sample dimension name with a group structure "
                    f"must start with a '/'. Got {value!r}"
                )

            if value.count("/") == 1:
                value = value[1:]
            elif value.endswith("/"):
                raise ValueError(
                    "A netCDF sample dimension name with a group structure "
                    f"can't end with a '/'. Got {value!r}"
                )

        self._set_netcdf("sample_dimension", value)

    def nc_sample_dimension_groups(self):
        """Return the netCDF sample dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_sample_dimension_groups`,
                     `nc_set_sample_dimension_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_sample_dimension('element')
        >>> f.nc_sample_dimension_groups()
        ()
        >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        'element'

        >>> f.nc_set_sample_dimension('/forecast/model/element')
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_sample_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_sample_dimension_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_sample_dimension)

    def nc_set_sample_dimension_groups(self, groups):
        """Set the netCDF sample dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/`` characters
        then an empty sequence is returned, signifying the root group.

        An alternative technique for setting the group structure is to set
        the netCDF dimension name, with `nc_set_sample_dimension`, with
        the group structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_sample_dimension_groups`,
                     `nc_sample_dimension_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_sample_dimension('element')
        >>> f.nc_sample_dimension_groups()
        ()
        >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        'element'

        >>> f.nc_set_sample_dimension('/forecast/model/element')
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_sample_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_sample_dimension_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_sample_dimension,
            nc_set=self.nc_set_sample_dimension,
            nc_groups=self.nc_sample_dimension_groups,
        )

    def nc_clear_sample_dimension_groups(self):
        """Remove the netCDF sample dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/`` characters
        then an empty sequence is returned, signifying the root group.

        An alternative technique for removing the group structure is to
        set the netCDF dimension name, with `nc_set_sample_dimension`,
        with no ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_sample_dimension_groups`,
                     `nc_set_sample_dimension_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_sample_dimension('element')
        >>> f.nc_sample_dimension_groups()
        ()
        >>> f.nc_set_sample_dimension_groups(['forecast', 'model'])
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_sample_dimension()
        'element'

        >>> f.nc_set_sample_dimension('/forecast/model/element')
        >>> f.nc_sample_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_sample_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_sample_dimension_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_sample_dimension,
            nc_set=self.nc_set_sample_dimension,
            nc_groups=self.nc_sample_dimension_groups,
        )


class NetCDFGlobalAttributes(NetCDFMixin):
    """Mixin class for accessing netCDF global attributes.

    .. versionadded:: (cfdm) 1.7.0

    """

    def nc_global_attributes(self, values=False):
        """Returns properties to write as netCDF global attributes.

        When multiple field constructs are being written to the same file,
        it is only possible to create a netCDF global attribute from a
        property that has identical values for each field construct. If
        any field construct's property has a different value then the
        property will not be written as a netCDF global attribute, even if
        it has been selected as such, but will appear instead as
        attributes on the netCDF data variables corresponding to each
        field construct.

        The standard description-of-file-contents properties are always
        written as netCDF global attributes, if possible, so selecting
        them is optional.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `write`, `nc_clear_global_attributes`,
                     `nc_set_global_attribute`, `nc_set_global_attributes`

        :Parameters:

            values: `bool`, optional
                Return the value (rather than `None`) for any global
                attribute that has, by definition, the same value as a
                construct property.

                .. versionadded:: (cfdm) 1.8.2

        :Returns:

            `dict`
                The selection of properties requested for writing to
                netCDF global attributes.

        **Examples**

        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None}
        >>> f.nc_set_global_attribute('foo')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None, 'foo': None}
        >>> f.nc_set_global_attribute('comment', 'global comment')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_global_attributes(values=True)
        {'Conventions': 'CF-1.12', 'comment': 'global_comment', 'foo': 'bar'}
        >>> f.nc_clear_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_global_attributes()
        {}

        """
        out = self._get_netcdf().get("global_attributes")

        if out is None:
            return {}

        out = out.copy()

        if values:
            # Replace a None value with the value from the variable
            # properties
            properties = self.properties()
            if properties:
                for prop, value in out.items():
                    if value is None and prop in properties:
                        out[prop] = properties[prop]

        return out

    def nc_clear_global_attributes(self):
        """Removes properties to write as netCDF global attributes.

        When multiple field constructs are being written to the same
        file, it is only possible to create a netCDF global attribute
        from a property that has identical values for each field
        construct. If any field construct's property has a different
        value then the property will not be written as a netCDF global
        attribute, even if it has been selected as such, but will
        appear instead as attributes on the netCDF data variables
        corresponding to each field construct.

        The standard description-of-file-contents properties are
        always written as netCDF global attributes, if possible, so
        selecting them is optional.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `write`, `nc_global_attributes`,
                     `nc_set_global_attribute`, `nc_set_global_attributes`

        :Returns:

            `dict`
                The removed selection of properties requested for
                writing to netCDF global attributes.

        **Examples**

        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None}
        >>> f.nc_set_global_attribute('foo')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None, 'foo': None}
        >>> f.nc_set_global_attribute('comment', 'global comment')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_clear_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_global_attributes()
        {}

        """
        out = self._get_netcdf().get("global_attributes")

        if out is None:
            out = {}

        self._set_netcdf("global_attributes", {})
        return out

    def nc_set_global_attribute(self, prop, value=None):
        """Select a property to be written as a netCDF global attribute.

        When multiple field constructs are being written to the same file,
        it is only possible to create a netCDF global attribute from a
        property that has identical values for each field construct. If
        any field construct's property has a different value then the
        property will not be written as a netCDF global attribute, even if
        it has been selected as such, but will appear instead as
        attributes on the netCDF data variables corresponding to each
        field construct.

        The standard description-of-file-contents properties are always
        written as netCDF global attributes, if possible, so selecting
        them is optional.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `write`, `nc_global_attributes`,
                     `nc_clear_global_attributes`,
                     `nc_set_global_attributes`

        :Parameters:

            prop: `str`
                Select the property to be written (if possible) as a
                netCDF global attribute.

            value: optional
                The value of the netCDF global attribute, which will be
                created (if possible) in addition to the property as
                written to a netCDF data variable. If unset (or `None`)
                then this acts as an instruction to write the property (if
                possible) to a netCDF global attribute instead of to a
                netCDF data variable.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None}
        >>> f.nc_set_global_attribute('foo')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None, 'foo': None}
        >>> f.nc_set_global_attribute('comment', 'global comment')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_clear_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_global_attributes()
        {}

        """
        out = self._get_netcdf().get("global_attributes")

        if out is None:
            out = {}

        out[prop] = value

        self._set_netcdf("global_attributes", out)

    def nc_set_global_attributes(self, properties, copy=True):
        """Set properties to be written as netCDF global attributes.

        When multiple field constructs are being written to the same
        file, it is only possible to create a netCDF global attribute
        from a property that has identical values for each field
        construct. If any field construct's property has a different
        value then the property will not be written as a netCDF global
        attribute, even if it has been selected as such, but will
        appear instead as attributes on the netCDF data variables
        corresponding to each field construct.

        The standard description-of-file-contents properties are
        always written as netCDF global attributes, if possible, so
        selecting them is optional.

        .. versionadded:: (cfdm) 1.7.10

        .. seealso:: `write`, `nc_clear_global_attributes`,
                     `nc_global_attributes`, `nc_set_global_attribute`

        :Parameters:

            properties: `dict`
                Set the properties be written as a netCDF global
                attribute from the dictionary supplied. The value of a
                netCDF global attribute, which will be created (if
                possible) in addition to the property as written to a
                netCDF data variable. If a value of `None` is used
                then this acts as an instruction to write the property
                (if possible) to a netCDF global attribute instead of
                to a netCDF data variable.

                *Parameter example:*
                  ``properties={'Conventions': None, 'project': 'research'}``

            copy: `bool`, optional
                If False then any property values provided by the
                *properties* parameter are not copied before
                insertion. By default they are deep copied.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None}
        >>> f.nc_set_global_attributes({})
        >>> f.nc_set_global_attributes({'foo': None})
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': None, 'foo': None}
        >>> f.nc_set_global_attributes('comment', 'global comment')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': None}
        >>> f.nc_set_global_attributes('foo', 'bar')
        >>> f.nc_global_attributes()
        {'Conventions': None, 'comment': 'global_comment', 'foo': 'bar'}

        """
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        out = self._get_netcdf().get("global_attributes")
        if out is None:
            out = {}

        out.update(properties)

        self._set_netcdf("global_attributes", out)


class NetCDFGroupAttributes(NetCDFMixin):
    """Mixin class for accessing netCDF group attributes.

    .. versionadded:: (cfdm) 1.8.6

    """

    def nc_group_attributes(self, values=False):
        """Returns properties to write as netCDF group attributes.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `write`, `nc_clear_group_attributes`,
                     `nc_set_group_attribute`, `nc_set_group_attributes`

        :Parameters:

            values: `bool`, optional
                Return the value (rather than `None`) for any group
                attribute that has, by definition, the same value as a
                construct property.

        :Returns:

            `dict`
                The selection of properties requested for writing to
                netCDF group attributes.

        **Examples**

        >>> f.nc_group_attributes()
        {'comment': None}
        >>> f.nc_set_group_attribute('foo')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': None}
        >>> f.nc_set_group_attribute('foo', 'bar')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes(values=True)
        {'comment': 'forecast comment', 'foo': 'bar'}
        >>> f.nc_clear_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes()
        {}

        """
        out = self._get_netcdf().get("group_attributes")

        if out is None:
            return {}

        out = out.copy()

        if values:
            # Replace a None value with the value from the variable
            # properties
            properties = self.properties()
            if properties:
                for prop, value in out.items():
                    if value is None and prop in properties:
                        out[prop] = properties[prop]

        return out

    def nc_clear_group_attributes(self):
        """Removes properties to write as netCDF group attributes.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `write`, `nc_group_attributes`,
                     `nc_set_group_attribute`, `nc_set_group_attributes`

        :Returns:

            `dict`
                The removed selection of properties requested for writing
                to netCDF group attributes.

        **Examples**

        >>> f.nc_group_attributes()
        {'comment': None}
        >>> f.nc_set_group_attribute('foo')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': None}
        >>> f.nc_set_group_attribute('foo', 'bar')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes(values=True)
        {'comment': 'forecast comment', 'foo': 'bar'}
        >>> f.nc_clear_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes()
        {}

        """
        out = self._get_netcdf().get("group_attributes")

        if out is None:
            out = {}

        self._set_netcdf("group_attributes", {})
        return out

    def nc_set_group_attribute(self, prop, value=None):
        """Select a property to be written as a netCDF group attribute.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `write`, `nc_group_attributes`,
                     `nc_clear_group_attributes`,
                     `nc_set_group_attributes`

        :Parameters:

            prop: `str`
                Select the property to be written (if possible) as a
                netCDF group attribute.

            value: optional
                The value of the netCDF group attribute, which will be
                created (if possible) in addition to the property as
                written to a netCDF data variable. If unset (or
                `None`) then this acts as an instruction to write the
                property (if possible) to a netCDF group attribute
                instead of to a netCDF data variable.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_group_attributes()
        {'comment': None}
        >>> f.nc_set_group_attribute('foo')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': None}
        >>> f.nc_set_group_attribute('foo', 'bar')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes(values=True)
        {'comment': 'forecast comment', 'foo': 'bar'}
        >>> f.nc_clear_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes()
        {}

        """
        out = self._get_netcdf().get("group_attributes")

        if out is None:
            out = {}

        out[prop] = value

        self._set_netcdf("group_attributes", out)

    def nc_set_group_attributes(self, properties, copy=True):
        """Set properties to be written as netCDF group attributes.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `write`, `nc_clear_group_attributes`,
                     `nc_group_attributes`, `nc_set_group_attribute`

        :Parameters:

            properties: `dict`
                Set the properties be written as a netCDF group
                attribute from the dictionary supplied. The value of a
                netCDF group attribute, which will be created (if
                possible) in addition to the property as written to a
                netCDF data variable. If a value of `None` is used
                then this acts as an instruction to write the property
                (if possible) to a netCDF group attribute instead of
                to a netCDF data variable.

                *Parameter example:*
                  ``properties={'Conventions': None, 'project': 'research'}``

            copy: `bool`, optional
                If False then any property values provided by the
                *properties* parameter are not copied before
                insertion. By default they are deep copied.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_group_attributes()
        {'comment': None}
        >>> f.nc_set_group_attribute('foo')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': None}
        >>> f.nc_set_group_attribute('foo', 'bar')
        >>> f.nc_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes(values=True)
        {'comment': 'forecast comment', 'foo': 'bar'}
        >>> f.nc_clear_group_attributes()
        {'comment': None, 'foo': 'bar'}
        >>> f.nc_group_attributes()
        {}

        """
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        out = self._get_netcdf().get("group_attributes")
        if out is None:
            out = {}

        out.update(properties)

        self._set_netcdf("group_attributes", out)


class NetCDFUnlimitedDimensions(NetCDFMixin):
    """Mixin class for accessing netCDF unlimited dimensions.

    .. versionadded:: (cfdm) 1.7.0

    Deprecated at version 1.7.4

    """

    def nc_unlimited_dimensions(self):
        """Returns domain axes to write as netCDF unlimited dimensions.

        By default output netCDF dimensions are not unlimited.

        .. versionadded:: (cfdm) 1.7.0

        Deprecated at version 1.7.4

        .. seealso:: `write`, `nc_clear_unlimited_dimensions`,
                     `nc_set_unlimited_dimensions`

        :Returns:

            `set`
                The selection of domain axis constructs to be written as
                netCDF unlimited dimensions.

        **Examples**

        >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0'}
        >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_clear_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_unlimited_dimensions()
        set()

        """
        raise DeprecationError(
            "Field.nc_unlimited_dimensions was deprecated at version 1.7.4 "
            "and is no longer available. Use DomainAxis.nc_is_unlimited "
            "instead."
        )

    def nc_set_unlimited_dimensions(self, axes):
        """Selects domain axes to write as netCDF unlimited dimensions.

        By default output netCDF dimensions are not unlimited.

        .. versionadded:: (cfdm) 1.7.0

        Deprecated at version 1.7.4

        .. seealso:: `write`, `nc_unlimited_dimensions`,
                     `nc_clear_unlimited_dimensions`

        :Parameters:

            axes: sequence of `str`, optional
                Select the domain axis constructs from the sequence
                provided. Domain axis constructs are identified by their
                construct identifiers.

                *Parameter example:*
                  ``axes=['domainaxis0', 'domainaxis1']``

                *Parameter example:*
                  ``axes=()``

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0'}
        >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_clear_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_unlimited_dimensions()
        set()

        """
        raise DeprecationError(
            "Field.nc_set_unlimited_dimensions was deprecated at version "
            "1.7.4 and is no longer available."
            "Use DomainAxis.nc_set_unlimited instead."
        )

    def nc_clear_unlimited_dimensions(self):
        """Removes domain axes to write as netCDF unlimited dimensions.

        By default output netCDF dimensions are not unlimited.

        .. versionadded:: (cfdm) 1.7.0

        Deprecated at version 1.7.4

        .. seealso:: `write`, `nc_unlimited_dimensions`,
                     `nc_set_unlimited_dimensions`

        :Returns:

            `set`
                The selection of domain axis constructs that has been removed.

        **Examples**

        >>> f.nc_set_unlimited_dimensions(['domainaxis0'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0'}
        >>> f.nc_set_unlimited_dimensions(['domainaxis1'])
        >>> f.nc_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_clear_unlimited_dimensions()
        {'domainaxis0', 'domainaxis1'}
        >>> f.nc_unlimited_dimensions()
        set()

        """
        raise DeprecationError(
            "Field.nc_clear_unlimited_dimensions was deprecated at version "
            "1.7.4 and is no longer available."
            "Use DomainAxis.nc_set_unlimited instead."
        )


class NetCDFExternal(NetCDFMixin):
    """Mixin class for accessing the netCDF external variable status.

    .. versionadded:: (cfdm) 1.7.0

    """

    def nc_get_external(self):
        """Whether a construct matches an external netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_set_external`

        :Returns:

            `bool`
                The external status.

        **Examples**

        >>> c.nc_get_external()
        False
        >>> c.nc_set_external(True)
        >>> c.nc_get_external()
        True

        """
        return self._get_netcdf().get("external", False)

    def nc_set_external(self, external):
        """Set external status of a netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `nc_get_external`

        :Parameters:

            external: `bool`, optional
                Set the external status.

                *Parameter example:*
                  ``external=True``

        :Returns:

            `None`

        **Examples**

        >>> c.nc_get_external()
        False
        >>> c.nc_set_external(True)
        >>> c.nc_get_external()
        True

        """
        self._set_netcdf("external", bool(external))


class NetCDFGeometry(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin to access the netCDF geometry container variable name.

    .. versionadded:: (cfdm) 1.8.0

    """

    def nc_del_geometry_variable(self, default=ValueError()):
        """Remove the netCDF geometry container variable name.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `nc_get_geometry_variable`,
                     `nc_has_geometry_variable`,
                     `nc_set_geometry_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the netCDF
                dimension name has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str`
                The removed netCDF geometry container variable name.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry')
        >>> f.nc_has_geometry_variable()
        True
        >>> f.nc_get_geometry_variable()
        'geometry'
        >>> f.nc_del_geometry_variable()
        'geometry'
        >>> f.nc_has_geometry_variable()
        False
        >>> print(f.nc_get_geometry_variable(None))
        None
        >>> print(f.nc_del_geometry_variable(None))
        None

        """
        try:
            return self._get_netcdf().pop("geometry_variable")
        except KeyError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF "
                "geometry variable name",
            )

    def nc_get_geometry_variable(self, default=ValueError()):
        """Return the netCDF geometry container variable name.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `nc_del_geometry_variable`,
                     `nc_has_geometry_variable`,
                     `nc_set_geometry_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF dimension name has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str`
                The netCDF geometry container variable name.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry')
        >>> f.nc_has_geometry_variable()
        True
        >>> f.nc_get_geometry_variable()
        'geometry'
        >>> f.nc_del_geometry_variable()
        'geometry'
        >>> f.nc_has_geometry_variable()
        False
        >>> print(f.nc_get_geometry_variable(None))
        None
        >>> print(f.nc_del_geometry_variable(None))
        None

        """
        try:
            return self._get_netcdf()["geometry_variable"]
        except KeyError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no netCDF "
                "geometry variable name",
            )

    def nc_has_geometry_variable(self):
        """Whether a netCDF geometry container variable has a name.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `nc_del_geometry_variable`,
                     `nc_get_geometry_variable`,
                     `nc_set_geometry_variable`

        :Returns:
            `bool`
                `True` if the netCDF geometry container variable name has
                been set, otherwise `False`.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry')
        >>> f.nc_has_geometry_variable()
        True
        >>> f.nc_get_geometry_variable()
        'geometry'
        >>> f.nc_del_geometry_variable()
        'geometry'
        >>> f.nc_has_geometry_variable()
        False
        >>> print(f.nc_get_geometry_variable(None))
        None
        >>> print(f.nc_del_geometry_variable(None))
        None

        """
        return "geometry_variable" in self._get_netcdf()

    def nc_set_geometry_variable(self, value):
        """Set the netCDF geometry container variable name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `nc_del_geometry_variable`,
                     `nc_get_geometry_variable`,
                     `nc_has_geometry_variable`

        :Parameters:

            value: `str`
                The value for the netCDF geometry container variable name.

        :Returns:
            `None`

        **Examples**

        >>> f.nc_set_geometry_variable('geometry')
        >>> f.nc_has_geometry_variable()
        True
        >>> f.nc_get_geometry_variable()
        'geometry'
        >>> f.nc_del_geometry_variable()
        'geometry'
        >>> f.nc_has_geometry_variable()
        False
        >>> print(f.nc_get_geometry_variable(None))
        None
        >>> print(f.nc_del_geometry_variable(None))
        None

        """
        if not value or value == "/":
            raise ValueError(
                f"Invalid netCDF geometry variable name: {value!r}"
            )

        if "/" in value:
            if not value.startswith("/"):
                raise ValueError(
                    "A netCDF geometry variable name with a group structure "
                    f"must start with a '/'. Got {value!r}"
                )

            if value.count("/") == 1:
                value = value[1:]
            elif value.endswith("/"):
                raise ValueError(
                    "A netCDF geometry variable name with a group structure "
                    f"can't end with a '/'. Got {value!r}"
                )

        self._set_netcdf("geometry_variable", value)

    def nc_geometry_variable_groups(self):
        """Return the netCDF geometry variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_geometry_variable_groups`,
        `nc_set_geometry_variable_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry1')
        >>> f.nc_geometry_variable_groups()
        ()
        >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
        >>> f.nc_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        '/forecast/model/geometry1'
        >>> f.nc_clear_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        'geometry1'

        >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
        >>> f.nc_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
        '/forecast/model/geometry1'
        >>> f.nc_geometry_variable_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_geometry_variable)

    def nc_set_geometry_variable_groups(self, groups):
        """Set the netCDF geometry variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for setting the group structure is to
        set the netCDF variable name, with `nc_set_geometry_variable`,
        with the group structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_clear_geometry_variable_groups`,
                     `nc_geometry_variable_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry1')
        >>> f.nc_geometry_variable_groups()
        ()
        >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
        >>> f.nc_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        '/forecast/model/geometry1'
        >>> f.nc_clear_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        'geometry1'

        >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
        >>> f.nc_geometry__variablegroups()
        ('forecast', 'model')
        >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
        '/forecast/model/geometry1'
        >>> f.nc_geometry_variable_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_geometry_variable,
            nc_set=self.nc_set_geometry_variable,
            nc_groups=self.nc_geometry_variable_groups,
        )

    def nc_clear_geometry_variable_groups(self):
        """Remove the netCDF geometry variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for removing the group structure is
        to set the netCDF variable name, with
        `nc_set_geometry_variable`, with no ``/`` characters.

        .. versionadded:: (cfdm) 1.8.6

        .. seealso:: `nc_geometry_variable_groups`,
                     `nc_set_geometry_variable_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_geometry_variable('geometry1')
        >>> f.nc_geometry_variable_groups()
        ()
        >>> f.nc_set_geometry_variable_groups(['forecast', 'model'])
        >>> f.nc_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        '/forecast/model/geometry1'
        >>> f.nc_clear_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_geometry_variable()
        'geometry1'

        >>> f.nc_set_geometry_variable('/forecast/model/geometry1')
        >>> f.nc_geometry_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_geometry_variable('/forecast/model/geometry1')
        '/forecast/model/geometry1'
        >>> f.nc_geometry_variable_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_geometry_variable,
            nc_set=self.nc_set_geometry_variable,
            nc_groups=self.nc_geometry_variable_groups,
        )


class NetCDFChunks(NetCDFMixin):
    """Mixin class for accessing the netCDF dataset chunksizes.

    This class replaces the deprecated `NetCDFHDF5` class.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def nc_hdf5_chunksizes(self, todict=False):
        """Get the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.7.2

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_hdf5_chunksizes",
            "Use `nc_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_dataset_chunksizes(self, todict=False):
        """Get the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_clear_dataset_chunksizes`,
                     `nc_set_dataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Parameters:

            {{chunk todict: `bool`, optional}}

        :Returns:

            {{Returns nc_dataset_chunksizes}}

        **Examples**

        >>> d.shape
        (1, 96, 73)
        >>> d.nc_set_dataset_chunksizes([1, 35, 73])
        >>> d.nc_dataset_chunksizes()
        (1, 35, 73)
        >>> d.nc_dataset_chunksizes(todict=True)
        {0: 1, 1: 35, 2: 73}
        >>> d.nc_clear_dataset_chunksizes()
        (1, 35, 73)
        >>> d.nc_dataset_chunksizes()
        None
        >>> d.nc_set_dataset_chunksizes('contiguous')
        >>> d.nc_dataset_chunksizes()
        'contiguous'
        >>> d.nc_set_dataset_chunksizes('1 KiB')
        >>> d.nc_dataset_chunksizes()
        1024
        >>> d.nc_set_dataset_chunksizes(None)
        >>> d.nc_dataset_chunksizes()
        None

        """
        chunksizes = self._get_netcdf().get("dataset_chunksizes")
        if todict:
            if not isinstance(chunksizes, tuple):
                raise ValueError(
                    "Can only set todict=True when the dataset chunking "
                    "strategy comprises the maximum number of array elements "
                    f"in a chunk along each data axis. Got: {chunksizes!r}"
                )

            chunksizes = {n: value for n, value in enumerate(chunksizes)}

        return chunksizes

    def nc_clear_hdf5_chunksizes(self):
        """Clear the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_clear_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.7.2

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_clear_hdf5_chunksizes",
            "Use `nc_clear_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_clear_dataset_chunksizes(self):
        """Clear the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_set_dataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Returns:

            `None` or `str` or `int` or `tuple` of `int`
                The chunking strategy prior to being cleared, as would
                be returned by `nc_dataset_chunksizes`.


        **Examples**

        >>> d.shape
        (1, 96, 73)
        >>> d.nc_set_dataset_chunksizes([1, 35, 73])
        >>> d.nc_clear_dataset_chunksizes()
        (1, 35, 73)
        >>> d.nc_set_dataset_chunksizes('1 KiB')
        >>> d.nc_clear_dataset_chunksizes()
        1024
        >>> d.nc_set_dataset_chunksizes(None)
        >>> print(d.nc_clear_dataset_chunksizes())
        None

        """
        return self._get_netcdf().pop("dataset_chunksizes", None)

    def nc_set_hdf5_chunksizes(self, chunksizes):
        """Set the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.7.2

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_set_hdf5_chunksizes",
            "Use `nc_set_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_set_dataset_chunksizes(self, chunksizes):
        """Set the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_clear_dataset_chunksizes`,
                     `{{package}}.read`, `{{package}}.write`

        :Parameters:

            {{chunk chunksizes}}

                  Each dictionary key is an integer that specifies an
                  axis by its position in the data array.

        :Returns:

            `None`

        **Examples**

        >>> d.shape
        (1, 96, 73)
        >>> d.nc_set_dataset_chunksizes([1, 35, 73])
        >>> d.nc_dataset_chunksizes()
        (1, 35, 73)
        >>> d.nc_clear_dataset_chunksizes()
        (1, 35, 73)
        >>> d.nc_dataset_chunksizes()
        None
        >>> d.nc_set_dataset_chunksizes('contiguous')
        >>> d.nc_dataset_chunksizes()
        'contiguous'
        >>> d.nc_set_dataset_chunksizes('1 KiB')
        >>> d.nc_dataset_chunksizes()
        1024
        >>> d.nc_set_dataset_chunksizes(None)
        >>> d.nc_dataset_chunksizes()
        None
        >>> d.nc_set_dataset_chunksizes([9999, -1, None])
        >>> d.nc_dataset_chunksizes()
        (1, 96, 73)
        >>> d.nc_clear_dataset_chunksizes()
        (1, 96, 73)
        >>> d.nc_set_dataset_chunksizes({1: 24})
        >>> d.nc_dataset_chunksizes()
        (1, 24, 73)
        >>> d.nc_set_dataset_chunksizes({0: None, 2: 50})
        >>> d.nc_dataset_chunksizes()
        (1, 24, 50)

        """
        if chunksizes is None:
            self.nc_clear_dataset_chunksizes()
            return

        shape = self.shape

        # Convert a dictionary to a sequence.
        if isinstance(chunksizes, dict):
            org_chunksizes = self.nc_dataset_chunksizes()
            if not isinstance(org_chunksizes, tuple):
                org_chunksizes = shape

            chunksizes = [
                chunksizes.get(n, j) for n, j in enumerate(org_chunksizes)
            ]

        if chunksizes != "contiguous":
            try:
                chunksizes = parse_bytes(chunksizes)
            except ValueError:
                raise ValueError(
                    f"Invalid chunksizes specification: {chunksizes!r}"
                )
            except AttributeError:
                # If chunksizes is a sequence then an AttributeError
                # will have been raised, rather than a ValueError.
                try:
                    chunksizes = tuple(chunksizes)
                except TypeError:
                    raise ValueError(
                        f"Invalid chunksizes specification: {chunksizes!r}"
                    )

                if len(chunksizes) != len(shape):
                    raise ValueError(
                        f"When chunksizes is a sequence {chunksizes!r} then "
                        "it must have the same length as the number of "
                        f"data dimensions ({len(shape)})"
                    )

                c = []
                for n, (i, j) in enumerate(zip(chunksizes, shape)):
                    if not (
                        i is None
                        or (isinstance(i, Integral) and (i > 0 or i == -1))
                    ):
                        raise ValueError(
                            f"Chunksize for dimension position {n} must be "
                            f"None, -1, or a positive integer. Got {i!r}"
                        )

                    if i is None or i == -1 or i > j:
                        # Set the chunk size to the dimension size
                        i = j
                    else:
                        # Make sure the chunk size is an integer
                        i = int(i)

                    c.append(i)

                chunksizes = tuple(c)

        self._set_netcdf("dataset_chunksizes", chunksizes)


class NetCDFHDF5(NetCDFMixin):
    """Mixin class for accessing the netCDF HDF5 chunksizes.

    Deprecated at version 1.12.2.0 and is no longer available. Use
    `NetCDFChunks` instead.

    .. versionadded:: (cfdm) 1.7.2

    """


class NetCDFUnlimitedDimension(NetCDFMixin):
    """Mixin class for accessing a netCDF unlimited dimension.

    .. versionadded:: (cfdm) 1.7.4

    """

    def nc_is_unlimited(self):
        """Inspect the unlimited status of the a netCDF dimension.

        By default output netCDF dimensions are not unlimited. The
        status is used by the `write` function.

        .. versionadded:: (cfdm) 1.7.4

        .. seealso:: `nc_set_unlimited`

        :Returns:

            `bool`
                The existing unlimited status. True and False signify
                "unlimited" and "not unlimited" respectively.

        **Examples**

        >>> da = f.domain_axis('domainaxis1')
        >>> da.nc_is_unlimited()
        False
        >>> da.nc_set_unlimited(True)
        >>> da.nc_is_unlimited()
        True
        >>> da.nc_set_unlimited(False)
        False
        >>> da.nc_is_unlimited()
        True

        """
        return self._get_netcdf().get("unlimited", False)

    def nc_set_unlimited(self, value):
        """Set the unlimited status of the a netCDF dimension.

        By default output netCDF dimensions are not unlimited. The
        status is used by the `write` function.

        .. versionadded:: (cfdm) 1.7.4

        .. seealso:: `nc_is_unlimited`

        :Parameters:

            value: `bool`
                The new unlimited status. True and False signify
                "unlimited" and "not unlimited" respectively.

        :Returns:

            `None`

        **Examples**

        >>> da = f.domain_axis('domainaxis1')
        >>> da.nc_is_unlimited()
        False
        >>> da.nc_set_unlimited(True)
        >>> da.nc_is_unlimited()
        True
        >>> da.nc_set_unlimited(False)
        False
        >>> da.nc_is_unlimited()
        True

        """
        self._set_netcdf("unlimited", bool(value))


class NetCDFComponents(NetCDFMixin):
    """Mixin class for a netCDF feature common to many constructs.

    Accesses netCDF names consistently across multiple metadata
    constructs.

    Assumes that the mixin classes `NetCDFDimension` and
    `NetCDFVariable` have also been subclassed.

    Assumes that the methods `_get_data_compression_variables` and
    `_get_coordinate_geometry_variables` have been defined elsewhere.

    .. versionadded:: (cfdm) 1.8.9.0

    """

    def nc_set_component_variable(self, component, value):
        """Set the netCDF variable name for components.

        Sets the netCDF variable name for all components of a given
        type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_variable`,
                     `nc_set_component_variable_groups`,
                     `nc_clear_component_variable_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates


                ``'node_count'``       Node count variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays

                ``'list'``             List variables for compression
                                       by gathering
                =====================  ===============================

            value: `str`
                The netCDF variable name to be set for each component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_variable('interior_ring', 'interiorring_1')

        """
        if component in ("count", "index", "list"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "node_count", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_variable(value)

    def nc_del_component_variable(self, component):
        """Remove the netCDF variable name of components.

        Removes the netCDF variable name for all components of a given
        type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_set_component_variable`,
                     `nc_set_component_variable_groups`,
                     `nc_clear_component_variable_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'node_count'``       Node count variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays

                ``'list'``             List variables for compression
                                       by gathering
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_del_component_variable('interior_ring')

        """
        if component in ("count", "index", "list"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "node_count", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_del_variable(None)

    def nc_set_component_variable_groups(self, component, groups):
        """Set the netCDF variable groups of components.

        Sets the netCDF variable groups for all components of a given
        type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_variable`,
                     `nc_set_component_variable`,
                     `nc_clear_component_variable_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'node_count'``       Node count variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays

                ``'list'``             List variables for compression
                                       by gathering
                =====================  ===============================

            groups: sequence of `str`
                The new group structure for each component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_variable_groups('interior_ring', ['forecast'])

        """
        if component in ("count", "index", "list"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "node_count", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_variable_groups(groups)

    def nc_clear_component_variable_groups(self, component):
        """Remove the netCDF variable groups of components.

        Removes the netCDF variable groups for all components of a
        given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_variable`,
                     `nc_set_component_variable`,
                     `nc_set_component_variable_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'node_count'``       Node count variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays

                ``'list'``             List variables for compression
                                       by gathering
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_clear_component_variable_groups('interior_ring')

        """
        if component in ("count", "index", "list"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "node_count", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_clear_variable_groups()

    def nc_set_component_dimension(self, component, value):
        """Set the netCDF dimension name of components.

        Sets the netCDF dimension name for all components of a given
        type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_dimension`,
                     `nc_set_component_dimension_groups`,
                     `nc_clear_component_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

            value: `str`
                The netCDF dimension name to be set for each component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_dimension('interior_ring', 'part')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_dimension(value)

    def nc_del_component_dimension(self, component):
        """Remove the netCDF dimension name of components.

        Removes the netCDF dimension name for all components of a
        given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_set_component_dimension`,
                     `nc_set_component_dimension_groups`,
                     `nc_clear_component_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_del_component_dimension('interior_ring')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_del_dimension(None)

    def nc_set_component_dimension_groups(self, component, groups):
        """Set the netCDF dimension groups of components.

        Sets the netCDF dimension groups for all components of a given
        type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_dimension`,
                     `nc_set_component_dimension`,
                     `nc_clear_component_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

            groups: sequence of `str`
                The new group structure for each component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_dimension_groups('interior_ring', ['forecast'])

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_dimension_groups(groups)

    def nc_clear_component_dimension_groups(self, component):
        """Remove the netCDF dimension groups of components.

        Removes the netCDF dimension groups for all components of a
        given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_dimension`,
                     `nc_set_component_dimension`,
                     `nc_set_component_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'interior_ring'``    Interior ring variables for
                                       geometry coordinates

                ``'part_node_count'``  Part node count variables for
                                       geometry coordinates

                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_clear_component_dimension_groups('interior_ring')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        elif component in ("interior_ring", "part_node_count"):
            variables = self._get_coordinate_geometry_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_clear_dimension_groups()

    def nc_set_component_sample_dimension(self, component, value):
        """Set the netCDF sample dimension name of components.

        Sets the netCDF sample dimension name for all components of a
        given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_sample_dimension`,
                     `nc_set_component_sample_dimension_groups`,
                     `nc_clear_component_sample_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

            value: `str`
                The netCDF sample_dimension name to be set for each
                component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_sample_dimension('count', 'obs')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_sample_dimension(value)

    def nc_del_component_sample_dimension(self, component):
        """Remove the netCDF sample dimension name of components.

        Removes the netCDF sample dimension name for all components of
        a given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_set_component_sample_dimension`,
                     `nc_set_component_sample_dimension_groups`,
                     `nc_clear_component_sample_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_del_component_sample_dimension('count')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_del_sample_dimension(None)

    def nc_set_component_sample_dimension_groups(self, component, groups):
        """Set the netCDF sample dimension groups of components.

        Sets the netCDF sample dimension groups for all components of
        a given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_sample_dimension`,
                     `nc_set_component_sample_dimension`,
                     `nc_clear_component_sample_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

            groups: sequence of `str`
                The new group structure for each component.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_component_sample_dimension_groups('count', ['forecast'])

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_set_sample_dimension_groups(groups)

    def nc_clear_component_sample_dimension_groups(self, component):
        """Remove the netCDF sample dimension groups of components.

        Removes the netCDF sample dimension groups for all components
        of a given type.

        Some components exist within multiple constructs, but when
        written to a netCDF dataset the netCDF names associated with
        such components will be arbitrarily taken from one of
        them. The netCDF names can be set on all such occurrences
        individually, or preferably by using this method to ensure
        consistency across all such components.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `nc_del_component_sample_dimension`,
                     `nc_set_component_sample_dimension`,
                     `nc_set_component_sample_dimension_groups`

        :Parameters:

            component: `str`
                Specify the component type. One of:

                =====================  ===============================
                *component*            Description
                =====================  ===============================
                ``'count'``            Count variables for contiguous
                                       ragged arrays

                ``'index'``            Index variables for indexed
                                       ragged arrays
                =====================  ===============================

        :Returns:

            `None`

        **Examples**

        >>> f.nc_del_component_sample_dimension_groups('count')

        """
        if component in ("count", "index"):
            variables = self._get_data_compression_variables(component)
        else:
            raise ValueError(f"Invalid component: {component!r}")

        for v in variables:
            v.nc_clear_sample_dimension_groups()


class NetCDFUnreferenced:
    """Mixin class for constructs of unreferenced netCDF variables.

    .. versionadded:: (cfdm) 1.8.9.0

    """

    def __initialise_from_source(self, source, copy=True):
        """Initialise dataset compliance information from a source.

        This method is called by
        `_Container__parent_initialise_from_source`, which in turn is
        called by `cfdm.core.Container.__init__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            source:
                The object from which to extract the initialisation
                information. Typically, but not necessarily, a
                `{{class}}` object.

            copy: `bool`, optional
                If True (the default) then deep copy the
                initialisation information.

        :Returns:

            `None`

        """
        try:
            dc = source._get_component("dataset_compliance", None)
        except AttributeError:
            pass
        else:
            if dc is not None:
                self._set_component("dataset_compliance", dc, copy=copy)

    def _set_dataset_compliance(self, value, copy=True):
        """Set the dataset compliance report.

        Set the report of problems encountered whilst reading the
        construct from a dataset.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `dataset_compliance`

        :Parameters:

            value: `dict`
               The value of the ``dataset_compliance`` component. This
               will be deep copied.

            copy: `bool`, optional
                If False then the compliance report dictionary is not
                copied prior to insertion.

        :Returns:

            `None`

        **Examples**

        """
        self._set_component("dataset_compliance", value, copy=copy)

    def dataset_compliance(self, display=False):
        """Return the dataset compliance report.

        A report of problems encountered whilst reading the construct
        from a dataset.

        If the dataset is partially CF-compliant to the extent that it
        is not possible to unambiguously map an element of the netCDF
        dataset to an element of the CF data model, then a construct
        is still returned by the `read` function, but may be
        incomplete.

        Such "structural" non-compliance would occur, for example, if
        the ``coordinates`` attribute of a CF-netCDF data variable
        refers to another variable that does not exist, or refers to a
        variable that spans a netCDF dimension that does not apply to
        the data variable.

        Other types of non-compliance are not checked, such whether or
        not controlled vocabularies have been adhered to.

        When a dictionary is returned, the compliance report may be
        updated by changing the dictionary in-place.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `{{package}}.read`, `_set_dataset_compliance`

        :Parameters:

            display: `bool`, optional
                If True print the compliance report. By default the report
                is returned as a dictionary.

        :Returns:

            `None` or `dict`
                The report. If *display* is True then the report is
                printed and `None` is returned. Otherwise the report is
                returned as a dictionary.

        **Examples**

        If no problems were encountered, an empty dictionary is returned:

        >>> f = {{package}}.example_field(1)
        >>> cfdm.write(f, 'example.nc')
        >>> g = {{package}}.read('example.nc')[0]
        >>> g.dataset_compliance()
        {}

        """
        d = self._get_component("dataset_compliance", {})

        if not display:
            return d

        if not d:
            print(d)
            return

        for key0, value0 in d.items():
            print(f"{{{key0!r}:")
            print(f"    CF version: {value0['CF version']!r},")
            print(f"    dimensions: {value0['dimensions']!r},")
            print("    non-compliance: {")
            for key1, value1 in sorted(value0["non-compliance"].items()):
                for x in value1:
                    print(f"        {key1!r}: [")
                    vals = "\n             ".join(
                        [
                            f"{key2!r}: {value2!r},"
                            for key2, value2 in sorted(x.items())
                        ]
                    )
                    print(f"            {{{vals}}},")

                print("        ],")

            print("    },")


class NetCDFSubsampledDimension(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin class for accessing the netCDF subsampled dimension name.

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def nc_del_subsampled_dimension(self, default=ValueError()):
        """Remove the netCDF sample dimension name.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_get_subsampled_dimension`,
                     `nc_has_subsampled_dimension`,
                     `nc_set_subsampled_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF subsampled dimension name has not been set. If
                set to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The removed netCDF subsampled dimension name.

        **Examples**

        >>> f.nc_set_subsampled_dimension('time')
        >>> f.nc_has_subsampled_dimension()
        True
        >>> f.nc_get_subsampled_dimension()
        'time'
        >>> f.nc_del_subsampled_dimension()
        'time'
        >>> f.nc_has_subsampled_dimension()
        False
        >>> print(f.nc_get_subsampled_dimension(None))
        None
        >>> print(f.nc_del_subsampled_dimension(None))
        None

        """
        return self._nc_del("subsampled_dimension", default=default)

    def nc_get_subsampled_dimension(self, default=ValueError()):
        """Return the netCDF subsampled dimension name.

        .. versionadded:: (cfdm)  1.10.0.0

        .. seealso:: `nc_del_subsampled_dimension`,
                     `nc_has_subsampled_dimension`,
                     `nc_set_subsampled_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF subsampled dimension name has not been set. If
                set to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The netCDF subsampled dimension name.

        **Examples**

        >>> f.nc_set_subsampled_dimension('time')
        >>> f.nc_has_subsampled_dimension()
        True
        >>> f.nc_get_subsampled_dimension()
        'time'
        >>> f.nc_del_subsampled_dimension()
        'time'
        >>> f.nc_has_subsampled_dimension()
        False
        >>> print(f.nc_get_subsampled_dimension(None))
        None
        >>> print(f.nc_del_subsampled_dimension(None))
        None

        """
        return self._nc_get("subsampled_dimension", default=default)

    def nc_has_subsampled_dimension(self):
        """Whether the netCDF subsampled dimension name has been set.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_del_subsampled_dimension`,
                     `nc_get_subsampled_dimension`,
                     `nc_set_subsampled_dimension`

        :Returns:

            `bool`
                `True` if the netCDF subsampled dimension name has
                been set, otherwise `False`.

        **Examples**

        >>> f.nc_set_subsampled_dimension('time')
        >>> f.nc_has_subsampled_dimension()
        True
        >>> f.nc_get_subsampled_dimension()
        'time'
        >>> f.nc_del_subsampled_dimension()
        'time'
        >>> f.nc_has_subsampled_dimension()
        False
        >>> print(f.nc_get_subsampled_dimension(None))
        None
        >>> print(f.nc_del_subsampled_dimension(None))
        None

        """
        return self._nc_has("subsampled_dimension")

    def nc_set_subsampled_dimension(self, value):
        """Set the netCDF subsampled dimension name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_del_subsampled_dimension`,
                     `nc_get_subsampled_dimension`,
                     `nc_has_subsampled_dimension`

        :Parameters:

            value: `str`
                The value for the netCDF subsampled dimension name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_subsampled_dimension('time')
        >>> f.nc_has_subsampled_dimension()
        True
        >>> f.nc_get_subsampled_dimension()
        'time'
        >>> f.nc_del_subsampled_dimension()
        'time'
        >>> f.nc_has_subsampled_dimension()
        False
        >>> print(f.nc_get_subsampled_dimension(None))
        None
        >>> print(f.nc_del_subsampled_dimension(None))
        None

        """
        return self._nc_set("subsampled_dimension", value)

    def nc_subsampled_dimension_groups(self):
        """Return the netCDF subsampled dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_clear_subsampled_dimension_groups`,
                     `nc_set_subsampled_dimension_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_subsampled_dimension('element')
        >>> f.nc_subsampled_dimension_groups()
        ()
        >>> f.nc_set_subsampled_dimension_groups(['forecast', 'model'])
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        'element'

        >>> f.nc_set_subsampled_dimension('/forecast/model/element')
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_subsampled_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_subsampled_dimension_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_subsampled_dimension)

    def nc_set_subsampled_dimension_groups(self, groups):
        """Set the netCDF subsampled dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/`` characters
        then an empty sequence is returned, signifying the root group.

        An alternative technique for setting the group structure is to set
        the netCDF dimension name, with `nc_set_subsampled_dimension`, with
        the group structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_clear_subsampled_dimension_groups`,
                     `nc_subsampled_dimension_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_subsampled_dimension('element')
        >>> f.nc_subsampled_dimension_groups()
        ()
        >>> f.nc_set_subsampled_dimension_groups(['forecast', 'model'])
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        'element'

        >>> f.nc_set_subsampled_dimension('/forecast/model/element')
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_subsampled_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_subsampled_dimension_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_subsampled_dimension,
            nc_set=self.nc_set_subsampled_dimension,
            nc_groups=self.nc_subsampled_dimension_groups,
        )

    def nc_clear_subsampled_dimension_groups(self):
        """Remove the netCDF subsampled dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/`` characters
        then an empty sequence is returned, signifying the root group.

        An alternative technique for removing the group structure is to
        set the netCDF dimension name, with `nc_set_subsampled_dimension`,
        with no ``/`` characters.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_subsampled_dimension_groups`,
                     `nc_set_subsampled_dimension_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_subsampled_dimension('element')
        >>> f.nc_subsampled_dimension_groups()
        ()
        >>> f.nc_set_subsampled_dimension_groups(['forecast', 'model'])
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_subsampled_dimension()
        'element'

        >>> f.nc_set_subsampled_dimension('/forecast/model/element')
        >>> f.nc_subsampled_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_subsampled_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_subsampled_dimension_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_subsampled_dimension,
            nc_set=self.nc_set_subsampled_dimension,
            nc_groups=self.nc_subsampled_dimension_groups,
        )


class NetCDFInterpolationSubareaDimension(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin class for the netCDF interpolation subarea dimension name.

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def nc_del_interpolation_subarea_dimension(self, default=ValueError()):
        """Remove the netCDF interpolation subarea dimension name.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_get_interpolation_subarea_dimension`,
                     `nc_has_interpolation_subarea_dimension`,
                     `nc_set_interpolation_subarea_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF subsampled dimension name has not been set. If
                set to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The removed netCDF subsampled dimension name.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('time')
        >>> f.nc_has_interpolation_subarea_dimension()
        True
        >>> f.nc_get_interpolation_subarea_dimension()
        'time'
        >>> f.nc_del_interpolation_subarea_dimension()
        'time'
        >>> f.nc_has_interpolation_subarea_dimension()
        False
        >>> print(f.nc_get_interpolation_subarea_dimension(None))
        None
        >>> print(f.nc_del_interpolation_subarea_dimension(None))
        None

        """
        return self._nc_del("interpolation_subarea_dimension", default=default)

    def nc_get_interpolation_subarea_dimension(self, default=ValueError()):
        """Return the netCDF interpolation subarea dimension name.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_del_interpolation_subarea_dimension`,
                     `nc_has_interpolation_subarea_dimension`,
                     `nc_set_interpolation_subarea_dimension`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF subsampled dimension name has not been set. If
                set to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `str`
                The netCDF subsampled dimension name.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('time')
        >>> f.nc_has_interpolation_subarea_dimension()
        True
        >>> f.nc_get_interpolation_subarea_dimension()
        'time'
        >>> f.nc_del_interpolation_subarea_dimension()
        'time'
        >>> f.nc_has_interpolation_subarea_dimension()
        False
        >>> print(f.nc_get_interpolation_subarea_dimension(None))
        None
        >>> print(f.nc_del_interpolation_subarea_dimension(None))
        None

        """
        return self._nc_get("interpolation_subarea_dimension", default=default)

    def nc_has_interpolation_subarea_dimension(self):
        """Whether the netCDF interpolation subarea dimension is set.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_del_interpolation_subarea_dimension`,
                     `nc_get_interpolation_subarea_dimension`,
                     `nc_set_interpolation_subarea_dimension`

        :Returns:

            `bool`
                `True` if the netCDF subsampled dimension name has
                been set, otherwise `False`.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('time')
        >>> f.nc_has_interpolation_subarea_dimension()
        True
        >>> f.nc_get_interpolation_subarea_dimension()
        'time'
        >>> f.nc_del_interpolation_subarea_dimension()
        'time'
        >>> f.nc_has_interpolation_subarea_dimension()
        False
        >>> print(f.nc_get_interpolation_subarea_dimension(None))
        None
        >>> print(f.nc_del_interpolation_subarea_dimension(None))
        None

        """
        return "interpolation_subarea_dimension" in self._get_netcdf()

    def nc_set_interpolation_subarea_dimension(self, value):
        """Set the netCDF interpolation subarea dimension name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_del_interpolation_subarea_dimension`,
                     `nc_get_interpolation_subarea_dimension`,
                     `nc_has_interpolation_subarea_dimension`

        :Parameters:

            value: `str`
                The value for the netCDF subsampled dimension name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('time')
        >>> f.nc_has_interpolation_subarea_dimension()
        True
        >>> f.nc_get_interpolation_subarea_dimension()
        'time'
        >>> f.nc_del_interpolation_subarea_dimension()
        'time'
        >>> f.nc_has_interpolation_subarea_dimension()
        False
        >>> print(f.nc_get_interpolation_subarea_dimension(None))
        None
        >>> print(f.nc_del_interpolation_subarea_dimension(None))
        None

        """
        self._nc_set("interpolation_subarea_dimension", value)

    def nc_interpolation_subarea_dimension_groups(self):
        """Return the interpolation subarea dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_clear_interpolation_subarea_dimension_groups`,
                     `nc_set_interpolation_subarea_dimension_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()
        >>> f.nc_set_interpolation_subarea_dimension_groups(['forecast', 'model'])
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        'element'

        >>> f.nc_set_interpolation_subarea_dimension('/forecast/model/element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_interpolation_subarea_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()

        """
        return self._nc_groups(
            nc_get=self.nc_get_interpolation_subarea_dimension
        )

    def nc_set_interpolation_subarea_dimension_groups(self, groups):
        """Set the interpolation subarea dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for setting the group structure is to
        set the netCDF dimension name, with
        `nc_set_interpolation_subarea_dimension`, with the group
        structure delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_clear_interpolation_subarea_dimension_groups`,
                     `nc_interpolation_subarea_dimension_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()
        >>> f.nc_set_interpolation_subarea_dimension_groups(['forecast', 'model'])
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        'element'

        >>> f.nc_set_interpolation_subarea_dimension('/forecast/model/element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_interpolation_subarea_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_interpolation_subarea_dimension,
            nc_set=self.nc_set_interpolation_subarea_dimension,
            nc_groups=self.nc_interpolation_subarea_dimension_groups,
        )

    def nc_clear_interpolation_subarea_dimension_groups(self):
        """Remove the interpolation subarea dimension group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for removing the group structure is
        to set the netCDF dimension name, with
        `nc_set_interpolation_subarea_dimension`, with no ``/``
        characters.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `nc_interpolation_subarea_dimension_groups`,
                     `nc_set_interpolation_subarea_dimension_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_interpolation_subarea_dimension('element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()
        >>> f.nc_set_interpolation_subarea_dimension_groups(['forecast', 'model'])
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        '/forecast/model/element'
        >>> f.nc_clear_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_get_interpolation_subarea_dimension()
        'element'

        >>> f.nc_set_interpolation_subarea_dimension('/forecast/model/element')
        >>> f.nc_interpolation_subarea_dimension_groups()
        ('forecast', 'model')
        >>> f.nc_del_interpolation_subarea_dimension('/forecast/model/element')
        '/forecast/model/element'
        >>> f.nc_interpolation_subarea_dimension_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_interpolation_subarea_dimension,
            nc_set=self.nc_set_interpolation_subarea_dimension,
            nc_groups=self.nc_interpolation_subarea_dimension_groups,
        )


class NetCDFNodeCoordinateVariable(NetCDFMixin, NetCDFGroupsMixin):
    """Mixin for accessing the netCDF node coordinate variable name.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def nc_del_node_coordinate_variable(self, default=ValueError()):
        """Remove the netCDF node coordinate variable name.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_get_node_coordinate_variable`,
                     `nc_has_node_coordinate_variable`,
                     `nc_set_node_coordinate_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF node coordinate variable name has not been
                set. If set to an `Exception` instance then it will be
                raised instead.

        :Returns:

            `str`
                The removed netCDF node coordinate variable name.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('node_x')
        >>> f.nc_has_node_coordinate_variable()
        True
        >>> f.nc_get_node_coordinate_variable()
        'node_x'
        >>> f.nc_del_node_coordinate_variable()
        'node_x'
        >>> f.nc_has_node_coordinate_variable()
        False
        >>> print(f.nc_get_node_coordinate_variable(None))
        None
        >>> print(f.nc_del_node_coordinate_variable(None))
        None

        """
        return self._nc_del("node_coordinate_variable", default=default)

    def nc_get_node_coordinate_variable(self, default=ValueError()):
        """Return the netCDF node coordinate variable name.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_del_node_coordinate_variable`,
                     `nc_has_node_coordinate_variable`,
                     `nc_set_node_coordinate_variable`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                netCDF node coordinate variable name has not been
                set. If set to an `Exception` instance then it will be
                raised instead.

        :Returns:

            `str`
                The netCDF node coordinate variable name. If unset
                then *default* is returned, if provided.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('node_x')
        >>> f.nc_has_node_coordinate_variable()
        True
        >>> f.nc_get_node_coordinate_variable()
        'node_x'
        >>> f.nc_del_node_coordinate_variable()
        'node_x'
        >>> f.nc_has_node_coordinate_variable()
        False
        >>> print(f.nc_get_node_coordinate_variable(None))
        None
        >>> print(f.nc_del_node_coordinate_variable(None))
        None

        """
        return self._nc_get("node_coordinate_variable", default=default)

    def nc_has_node_coordinate_variable(self):
        """Whether the netCDF node coordinate variable name is set.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_get_node_coordinate_variable`,
                     `nc_del_node_coordinate_variable`,
                     `nc_set_node_coordinate_variable`

        :Returns:

            `bool`
                `True` if the netCDF node coordinate variable name has
                been set, otherwise `False`.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('node_x')
        >>> f.nc_has_node_coordinate_variable()
        True
        >>> f.nc_get_node_coordinate_variable()
        'node_x'
        >>> f.nc_del_node_coordinate_variable()
        'node_x'
        >>> f.nc_has_node_coordinate_variable()
        False
        >>> print(f.nc_get_node_coordinate_variable(None))
        None
        >>> print(f.nc_del_node_coordinate_variable(None))
        None

        """
        return "node_coordinate_variable" in self._get_netcdf()

    def nc_set_node_coordinate_variable(self, value):
        """Set the netCDF node coordinate variable name.

        If there are any ``/`` (slash) characters in the netCDF name
        then these act as delimiters for a group hierarchy. By
        default, or if the name starts with a ``/`` character and
        contains no others, the name is assumed to be in the root
        group.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_get_node_coordinate_variable`,
                     `nc_has_node_coordinate_variable`,
                     `nc_del_node_coordinate_variable`

        :Parameters:

            value: `str`
                The value for the netCDF node coordinate variable
                name.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_node_coordinate_variable('node_x')
        >>> f.nc_has_node_coordinate_variable()
        True
        >>> f.nc_get_node_coordinate_variable()
        'node_x'
        >>> f.nc_del_node_coordinate_variable()
        'node_x'
        >>> f.nc_has_node_coordinate_variable()
        False
        >>> print(f.nc_get_node_coordinate_variable(None))
        None
        >>> print(f.nc_del_node_coordinate_variable(None))
        None

        """
        return self._nc_set("node_coordinate_variable", value)

    def nc_node_coordinate_variable_groups(self):
        """Return the netCDF node coordinate variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_clear_node_coordinate_variable_groups`,
                     `nc_set_node_coordinate_variable_groups`

        :Returns:

            `tuple` of `str`
                The group structure.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('time')
        >>> f.nc_node_coordinate_variable_groups()
        ()
        >>> f.nc_set_node_coordinate_variable_groups(['forecast', 'model'])
        >>> f.nc_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_node_coordinate_variable()
        '/forecast/model/time'
        >>> f.nc_clear_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_node_coordinate_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_node_coordinate_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_node_coordinate_variable_groups()
        ()

        """
        return self._nc_groups(nc_get=self.nc_get_node_coordinate_variable)

    def nc_set_node_coordinate_variable_groups(self, groups):
        """Set the netCDF node_coordinate_variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for setting the group structure is to
        set the netCDF node coordinate variable name, with
        `nc_set_node_coordinate_variable`, with the group structure
        delimited by ``/`` characters.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_clear_node_coordinate_variable_groups`,
                     `nc_node_coordinate_variable_groups`

        :Parameters:

            groups: sequence of `str`
                The new group structure.

        :Returns:

            `tuple` of `str`
                The group structure prior to being reset.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('time')
        >>> f.nc_node_coordinate_variable_groups()
        ()
        >>> f.nc_set_node_coordinate_variable_groups(['forecast', 'model'])
        >>> f.nc_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_node_coordinate_variable()
        '/forecast/model/time'
        >>> f.nc_clear_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_node_coordinate_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_node_coordinate_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_node_coordinate_variable_groups()
        ()

        """
        return self._nc_set_groups(
            groups,
            nc_get=self.nc_get_node_coordinate_variable,
            nc_set=self.nc_set_node_coordinate_variable,
            nc_groups=self.nc_node_coordinate_variable_groups,
        )

    def nc_clear_node_coordinate_variable_groups(self):
        """Remove the netCDF node coordinate variable group hierarchy.

        The group hierarchy is defined by the netCDF name. Groups are
        delimited by ``/`` (slash) characters in the netCDF name. The
        groups are returned, in hierarchical order, as a sequence of
        strings. If the name is not set, or contains no ``/``
        characters then an empty sequence is returned, signifying the
        root group.

        An alternative technique for removing the group structure is
        to set the netCDF node coordinate variable name, with
        `nc_set_node_coordinate_variable`, with no ``/`` characters.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `nc_node_coordinate_variable_groups`,
                     `nc_set_node_coordinate_variable_groups`

        :Returns:

            `tuple` of `str`
                The removed group structure.

        **Examples**

        >>> f.nc_set_node_coordinate_variable('time')
        >>> f.nc_node_coordinate_variable_groups()
        ()
        >>> f.nc_set_node_coordinate_variable_groups(['forecast', 'model'])
        >>> f.nc_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_node_coordinate_variable()
        '/forecast/model/time'
        >>> f.nc_clear_node_coordinate_variable_groups()
        ('forecast', 'model')
        >>> f.nc_get_variable()
        'time'

        >>> f.nc_set_node_coordinate_variable('/forecast/model/time')
        >>> f.nc_variable_groups()
        ('forecast', 'model')
        >>> f.nc_del_node_coordinate_variable('/forecast/model/time')
        '/forecast/model/time'
        >>> f.nc_node_coordinate_variable_groups()
        ()

        """
        return self._nc_clear_groups(
            nc_get=self.nc_get_node_coordinate_variable,
            nc_set=self.nc_set_node_coordinate_variable,
            nc_groups=self.nc_node_coordinate_variable_groups,
        )


class NetCDFAggregation(NetCDFMixin):
    """Mixin class for netCDF aggregated variables.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def nc_del_aggregated_data(self):
        """Remove the netCDF aggregated_data terms.

        The aggregated data terms define the names of the fragment
        array variables, as would be stored in a netCDF file in an
        "aggregated_data" attribute.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_get_aggregated_data`,
                     `nc_has_aggregated_data`,
                     `nc_set_aggregated_data`

        :Returns:

            `dict`
                The removed netCDF aggregated_data elements in a
                dictionary whose key/value pairs are the feature names
                and their corresponding fragment array variable names.

        **Examples**

        >>> f.nc_set_aggregated_data(
        ...     {'map': 'fragment_map',
        ...      'uris': 'fragment_uris',
        ...      'identifiers': 'fragment_identifiers'}
        ... )
        >>> f.nc_has_aggregated_data()
        True
        >>> f.nc_get_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_del_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_has_aggregated_data()
        False
        >>> f.nc_del_aggregated_data()
        {}
        >>> f.nc_get_aggregated_data()
        {}
        >>> f.nc_set_aggregated_data(
        ...     'map: fragment_map, uris: fragment_uris identifiers: fragment_idenfiers'
        ... )

        """
        out = self._nc_del("aggregated_data", None)
        if out is None:
            return {}

        return out.copy()

    def nc_get_aggregated_data(self):
        """Return the netCDF aggregated data terms.

        The aggregated data terms define the names of the fragment
        array variables, and are stored in a netCDF file in an
        "aggregated_data" attribute.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregated_data`,
                     `nc_has_aggregated_data`,
                     `nc_set_aggregated_data`

        :Returns:

            `dict`
                The netCDF aggregated_data terms in a dictionary whose
                key/value pairs are the feature names and their
                corresponding fragment array variable names.

        **Examples**

        >>> f.nc_set_aggregated_data(
        ...     {'map': 'fragment_map',
        ...      'uris': 'fragment_uris',
        ...      'identifiers': 'fragment_identifiers'}
        ... )
        >>> f.nc_has_aggregated_data()
        True
        >>> f.nc_get_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_del_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_has_aggregated_data()
        False
        >>> f.nc_del_aggregated_data()
        {}
        >>> f.nc_get_aggregated_data()
        {}
        >>> f.nc_set_aggregated_data(
        ...     'map: fragment_map, uris: fragment_uris identifiers: fragment_idenfiers'
        ... )

        """
        out = self._nc_get("aggregated_data", None)
        if out is None:
            return {}

        return out.copy()

    def nc_has_aggregated_data(self):
        """Whether any netCDF aggregated_data terms have been set.

        The aggregated data terms define the names of the fragment
        array variables, and are stored in a netCDF file in an
        "aggregated_data" attribute.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregated_data`,
                     `nc_get_aggregated_data`,
                     `nc_set_aggregated_data`

        :Returns:

            `bool`
                `True` if the netCDF aggregated_data terms have been
                set, otherwise `False`.

        **Examples**

        >>> f.nc_set_aggregated_data(
        ...     {'map': 'fragment_map',
        ...      'uris': 'fragment_uris',
        ...      'identifiers': 'fragment_identifiers'}
        ... )
        >>> f.nc_has_aggregated_data()
        True
        >>> f.nc_get_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_del_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_has_aggregated_data()
        False
        >>> f.nc_del_aggregated_data()
        {}
        >>> f.nc_get_aggregated_data()
        {}
        >>> f.nc_set_aggregated_data(
        ...     'map: fragment_map, uris: fragment_uris identifiers: fragment_idenfiers'
        ... )

        """
        return self._nc_has("aggregated_data")

    def nc_set_aggregated_data(self, value):
        """Set the netCDF aggregated_data elements.

        The aggregated data terms define the names of the fragment
        array variables, and are stored in a netCDF file in an
        "aggregated_data" attribute.

        If there are any ``/`` (slash) characters in the netCDF
        variable names then these act as delimiters for a group
        hierarchy. By default, or if the name starts with a ``/``
        character and contains no others, the name is assumed to be in
        the root group.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregated_data`,
                     `nc_get_aggregated_data`,
                     `nc_has_aggregated_data`

        :Parameters:

            value: `dict` or `str`
                The netCDF aggregated_data terms in a dictionary whose
                key/value pairs are the feature names and their
                corresponding fragment array variable names; or else
                an equivalent string formatted with the the CF-netCDF
                encoding.

        :Returns:

            `None`

        **Examples**

        >>> f.nc_set_aggregated_data(
        ...     {'map': 'fragment_map',
        ...      'uris': 'fragment_uris',
        ...      'identifiers': 'fragment_identifiers'}
        ... )
        >>> f.nc_has_aggregated_data()
        True
        >>> f.nc_get_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_del_aggregated_data()
        {'map': 'fragment_map',
         'uris': 'fragment_uris',
         'identifiers': 'fragment_identifiers'}
        >>> f.nc_has_aggregated_data()
        False
        >>> f.nc_del_aggregated_data()
        {}
        >>> f.nc_get_aggregated_data()
        {}
        >>> f.nc_set_aggregated_data(
        ...     'map: fragment_map, uris: fragment_uris identifiers: fragment_idenfiers'
        ... )

        """
        if not value:
            self.nc_del_aggregated_data()

        if isinstance(value, str):
            v = split(r"\s+", value)
            value = {term[:-1]: var for term, var in zip(v[::2], v[1::2])}
        else:
            # 'value' is a dictionary
            value = value.copy()

        self._set_netcdf("aggregated_data", value)

    def _nc_del_aggregation_fragment_type(self):
        """Remove the type of fragments in the aggregated data.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `str` or `None`
                The removed fragment type, either ``'uri'`` for
                fragment datasets, or ``'unique_value'`` for fragment
                unique values, or `None` if no fragment type was set.

        """
        return self._nc_del("aggregation_fragment_type", None)

    def nc_get_aggregation_fragment_type(self):
        """The type of fragments in the aggregated data.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `str` or `None`
                The fragment type, either ``'uri'`` for fragment
                datasets, or ``'unique_value'`` for fragment unique
                values, or `None` for an unspecified fragment type.

        """
        return self._nc_get("aggregation_fragment_type", None)

    def _nc_set_aggregation_fragment_type(self, value):
        """Set the type of fragments in the aggregated data.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            value: `str` or `None`
                The fragment type, either ``'uri'`` for fragment
                files, ``'unique_value'`` for fragment unique values,
                or `None` for an unspecified fragment type.

        :Returns:

            `None`

        """
        self._set_netcdf("aggregation_fragment_type", value)
        if value == "unique_value":
            self._nc_set_aggregation_write_status(True)

    def nc_del_aggregation_write_status(self):
        """Set the netCDF aggregation write status to `False`.

        A necessary (but not sufficient) condition for writing the
        data as CF-netCDF aggregated data is that the write status is
        True.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_get_aggregation_write_status`,
                     `nc_set_aggregation_write_status`

        :Returns:

            `bool`
                The netCDF aggregation write status prior to deletion.

        """
        return self._nc_del("aggregation_write_status", False)

    def nc_get_aggregation_write_status(self):
        """Get the netCDF aggregation write status.

        A necessary (but not sufficient) condition for writing the
        data as CF-netCDF aggregated data is that the write status is
        True.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregation_write_status`,
                     `nc_set_aggregation_write_status`

        :Returns:

            `bool`
                The netCDF aggregation write status.

        """
        status = self._nc_get("aggregation_write_status", False)
        if (
            not status
            and self.nc_get_aggregation_fragment_type() == "unique_value"
        ):
            status = True
            self._nc_set_aggregation_write_status(status)

        return status

    def _nc_set_aggregation_write_status(self, status):
        """Set the netCDF aggregation write status.

        A necessary (but not sufficient) condition for writing the
        data as CF-netCDF aggregated data is that the write status is
        True.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregation_write_status`,
                     `nc_get_aggregation_write_status`,
                     `nc_set_aggregation_write_status`

        :Parameters:

            status: `bool`
                The new write status.

        :Returns:

            `None`

        """
        self._set_netcdf("aggregation_write_status", bool(status))

    def nc_set_aggregation_write_status(self, status):
        """Set the netCDF aggregation write status.

        A necessary (but not sufficient) condition for writing the
        data as CF-netCDF aggregated data is that the write status is
        True.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregation_write_status`,
                     `nc_get_aggregation_write_status`

        :Parameters:

            status: `bool`
                The new write status.

        :Returns:

            `None`

        """
        if status:
            raise ValueError(
                "'nc_set_aggregation_write_status' only allows the netCDF "
                "aggregation write status to be set to False. At your own "
                "risk you may use '_nc_set_aggregation_write_status' to set "
                "the status to True."
            )

        self._nc_set_aggregation_write_status(status)
