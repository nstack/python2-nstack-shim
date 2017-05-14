from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import map
from future import standard_library
standard_library.install_aliases()
from builtins import *
from functools import partial, wraps
import uniplate

from . import generic
from . import types

fst_ = lambda i: i[0]

def _named(cls, name):
    if name is None:
        return cls
    return type(name, (cls, ), {})

def _custom_builtin(cls, name=None, optional=False):
    if not optional:
        return _named(cls, name)
    return type(name or 'Optional({})'.format(cls), (cls, ), {
        '__new__': lambda cls2, val: None if val is None else cls.__new__(cls2, val)
    })

def _mutate_obj_methods(obj, handlers):
    for i,j in handlers.items():
        setattr(obj, i, j(getattr(obj, i)))
    return obj

def cast(typ, val):
    if issubclass(typ, types.NStackTypeInputMixin):
        return typ._nstackFromBase(val)
    return typ(val)

def preproc_sum(inp):
    chs = uniplate.abstract_children(generic.descend_types, inp)
    return [(lambda i: lambda v: cast(i, v))(i) for i in chs]

def preproc_iter(inp):
    chs = uniplate.abstract_children(generic.descend_types, inp)

    def cast_iter(bs):
        def inner(inp):
            cur, bs[:] = bs[0], bs[1:]
            return cast(cur, inp)
        return inner

    return lambda i: uniplate.descend(i, cast_iter(chs[:]))

def preproc_dict(inp, allow_missing=False):
    chs = uniplate.abstract_children(
        partial(generic.descend_types, include_fields=True),
        inp)

    if allow_missing:
        return lambda i: {j: cast(k, inp.get(j)) for j, k in chs}
    return lambda i: {j: cast(k, inp[j]) for j, k in chs}

def convert(inp, environment=False, name=None):
    environment = environment or {}
    o = inp.get('optional', False)

    t, r = inp['type']

    if t == 'ref':
        if isinstance(r, list):
            r = tuple(r)
        return environment[r]
    if t == 'sum':
        return types.createsum(name or "sum",
                               map(fst_, r),
                               preprocfuncs=preproc_sum(inp),
                               optional=o)
    if t == 'record':
        return types.createrecord(name or "record",
                                  map(fst_, r),
                                  preprocfunc=preproc_iter(inp),
                                  optional=o)
    if t == 'tuple':
        r = [(lambda i: i) for i in r]
        return types.createtuple(name or "tuple",
                                 len(r),
                                 preprocfunc=preproc_iter(inp),
                                 optional=o)
    if t == 'array':
        return types.createlist(name or "list",
                                preprocfunc=lambda i: (r(j) for j in i),
                                optional=o)
    if t == 'int':
        return _custom_builtin(int, name, optional=o)
    if t == 'double':
        return _custom_builtin(float, name, optional=o)
    if t == 'bool':
        return _custom_builtin(bool, name, optional=o)
    if t == 'bytearray':
        return _custom_builtin(bytes, name, optional=o)
    if t == 'text':
        return _custom_builtin(str, name, optional=o)
    # todo: missing some types

    raise TypeError("Unknown type {}".format(t))

# @convert.register(type(None))
# def convert_none(inp, environment=False, name=None):
#     # identity function
#     return lambda i: i

def transform_types(schema, environment=None):
    environment = environment or {}
    return uniplate.abstract_transform(generic.descend_types,
                                       schema,
                                       partial(convert, environment=environment))

def transform_named_types(name, schema, environment=None, add_to_environment=True):
    r = generic.descend_types(schema, partial(transform_types, environment=environment))
    # final layer at root:
    return convert(r, environment=environment, name=name)

def transform_sig_input(schema, environment=None):
    inp, out = schema
    return transform_types(inp, environment=environment)

def create_mutator(convert_func):
    def method_mutator(f):
        @wraps(f)
        def new_method(v):
            try:
                r = cast(convert_func, v)
            except Exception as e:
                # todo: fill out info and add stack-trace in
                raise TypeError("error converting types: {}".format(e))
            x = f(r)
            return uniplate.transform(x, uniplate.mktrans(types.NStackTypeOutputMixin,
                                                          lambda i: i._nstackToBase()))
        return new_method
    return method_mutator

def process_sigs_to_mutators(schema, environment=None):
    return uniplate.descend(schema, lambda i: create_mutator(transform_sig_input(
        i, environment=environment)))

def apply_sig_to_object(schema, obj, environment=None):
    return _mutate_obj_methods(
        obj,
        process_sigs_to_mutators(schema, environment=environment))

def schema_to_types(schema):
    env = {}
    for i, j in schema:
        nm, k = (i[1], tuple(i)) if isinstance(i, (list, tuple)) else (i, i)
        env[k] = transform_named_types(nm, j, env)
    return env

def process_schema(schema, applynsto=None):
    applynsto = applynsto or type('scope', (object, ), {})
    env = schema_to_types(schema.get('types', []))
    mut = lambda obj: apply_sig_to_object(schema.get('signatures'),
                                          obj,
                                          environment=env)
    for i, j in schema.get('imports', []):
        ns_ = type(i, (object,), {k[1]: l for k, l in env.items()
                                  if isinstance(k, tuple) and k[0] == j})
        setattr(applynsto, i, ns_)
    for i in schema.get('unqualified', []):
        for k, l in env.items():
            if isinstance(k, tuple) and k[0] == i:
                setattr(applynsto, k[1], l)
    for i, j in env.items():
        if not isinstance(i, tuple):
            setattr(applynsto, i, j)
    return (env, mut, applynsto)

