from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from future import standard_library
standard_library.install_aliases()
from builtins import *
from singledispatch import singledispatch

@singledispatch
def descend_types(inp, trans, **k):
    return None

@descend_types.register(dict)
def descend_types_dict(inp, trans, include_fields=False, **k):
    t, r = inp['type']
    if t == 'ref':
        return inp
    if t == 'sum':
        return dict(inp, type=[t, [[i, trans(j)] for i, j in r]])
    if t == 'record':
        if include_fields:
            # technically biplate in this case...
            return dict(inp, type=[t, [trans(tuple(i)) for i in r]])
        return dict(inp, type=[t, [[i, trans(j)] for i, j in r]])
    if t == 'tuple':
        return dict(inp, type=[t, [trans(i) for i in r]])
    if t == 'array':
        return dict(inp, type=[t, trans(r)])
    if t in ['int', 'double', 'bool', 'text', 'bytearray']:
        return inp
    raise TypeError("Unsupported type {}".format(t))
