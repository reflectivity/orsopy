import sys

from dataclasses import (_FIELD, _FIELD_INITVAR, _FIELDS, _HAS_DEFAULT_FACTORY, _POST_INIT_NAME, MISSING, _create_fn,
                         _field_init, _init_param, _set_new_attribute, dataclass, field, fields)

# change of signature introduced in python 3.10.1
if sys.version_info >= (3, 10, 1):
    _field_init_real = _field_init

    def _field_init(f, frozen, locals, self_name):
        return _field_init_real(f, frozen, locals, self_name, False)


elif sys.version_info < (3, 7, 0):
    # fix bug in python 3.6 when using default_factory for dataclass objects
    _orig_field = field

    def field(*args, **opts):
        if "default_factory" in opts and not opts["default_factory"] in [list, tuple]:
            return opts["default_factory"]()
        else:
            return _orig_field(*args, **opts)
