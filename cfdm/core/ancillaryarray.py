
# ====================================================================
#
# CFDM
#
# ====================================================================

class AncillaryArray(AbstractVariable):
    '''
    '''
    def dump(self, display=True, field=None, key=None,
             _omit_properties=(), _prefix='', _title=None,
             _create_title=True, _extra=(), _level=0):
        '''
        '''
        return super(AncillaryArray, self).dump(
            display=display,
            field=field, key=key,
            _omit_properties=_omit_properties,
            _prefix=_prefix, _title=_title,
            _create_title=_create_title, _extra=_extra,
            _level=_level)
    #--- End: def
    
#--- End: class
