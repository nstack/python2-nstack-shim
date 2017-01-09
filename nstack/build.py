from functools import partial, singledispatch, wraps
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
        '__new__': lambda cls, val: None if val is None else cls.__new__(cls, val)
    })

def _mutate_obj_methods(obj, handlers):
    for i,j in handlers:
        setattr(obj, i, j(getattr(obj, i)))

@singledispatch
def convert(inp, **k):
    raise TypeError("Fallback case for convert() with {}".format(inp))

@convert.register(dict)
def convert_dict(inp, environment=False, name=None):
    environment = environment or {}
    o = inp.get('optional', False)

    t, r = inp['type']

    if t == 'ref':
        return environment[r]
    if t == 'sum':
        return types.createsum(name or "UnnamedSum", map(fst_, r), optional=o)
    if t == 'record':
        return types.createrecord(name or "UnnamedRecord", map(fst_, r), optional=o)
    if t == 'tuple':
        r = [(lambda i: i) for i in r]
        return types.createtuple(name or "UnnamedTuple", len(r), optional=o)
    if t == 'array':
        return _custom_builtin(list, name, optional=o)
    if t == 'int':
        return _custom_builtin(int, name, optional=o)
    if t == 'double':
        return _custom_builtin(float, name, optional=o)
    if t == 'bool':
        return _custom_builtin(bool, name, optional=o)
    if t == 'bytearray':
        return lambda i: i # todo: bytes / bytearray . will we need to convert?
    # todo: missing some types

    raise TypeError("Unknown type {}".format(t))

# @convert.register(type(None))
# def convert_none(inp, environment=False, name=None):
#     # identity function
#     return lambda i: i

def cast_from_type(typ):
    if issubclass(typ, types.NStackTypeInputMixin):
        return lambda i: typ._nstackFromBase(i)
    return typ

def cast_tuple(builders):
    bs = builders
    def inner(inp):
        cur, bs[:] = bs[0], bs[1:]
        return cur(inp)
    return lambda i: uniplate.descend(i, inner)

def builder(inp, environment=None, name=None):
    typ = convert(inp, environment=environment, name=name)
    ctp = cast_from_type(typ)
    chs = lambda: uniplate.abstract_children(generic.descend_types, inp) # thunk!
    if issubclass(typ, types.SumBase):
        def sum_factory(value):
            if not value:
                return None
            branch, rawval = value
            newval = chs()[branch](rawval)
            return ctp((branch, newval))
        return sum_factory
    if issubclass(typ, types.RecordBase):
        # we can't be guaranteed the same order
        # so we pull out children with keys...
        chs = uniplate.abstract_children(partial(generic.descend_types,
                                                 include_fields=True), inp)
        return ctp({i: j(inp[i]) for i, j in chs.items()})
    if issubclass(typ, list):
        return lambda i: ctp(map(chs()[0], i))
    if issubclass(typ, tuple):
        return lambda i: ctp(cast_tuple(chs())(i))
    return ctp

def transform_types(schema, environment=None):
    environment = environment or {}
    return uniplate.abstract_transform(generic.descend_types,
                                       schema,
                                       partial(builder, environment=environment))

def transform_named_types(name, schema, environment=None, add_to_environment=True):
    r = generic.descend_types(schema, partial(transform_types, environment=environment))
    # final layer at root:
    return builder(r, environment=environment, name=name)

def transform_sig_input(schema, environment=None):
    inp, out = schema
    return transform_types(inp, environment=environment)

def create_mutator(convert_func):
    def method_mutator(f):
        @wraps(f)
        def new_method(v):
            try:
                r = convert_func(v)
            except Exception as e:
                # todo: fill out info and add stack-trace in
                raise TypeError("error converting types: {}".format(e))
            return f(r)
        return new_method
    return method_mutator

def process_sigs_to_mutators(schema, environment=None):
    return uniplate.descend(schema, lambda i: create_mutator(transform_sig_input(
        i, environment=environment)))

def apply_sig_to_object(schema, obj, environment=None):
    return _mutate_obj_methods(
        process_sigs_to_mutators(schema, environment=environment), obj)

def schema_to_types(schema):
    env = {}
    for i, j in schema.items():
        env[i] = transform_named_types(i, j, env)
    return env
