from functools import singledispatch

t_base = lambda x: {'type': x}
t_ = singledispatch(lambda x: t_base([x, []]))
t_.register(tuple,  lambda x: t_base(x[:2]))
t_.register(list,   lambda x: t_base(x[:2]))
tc_ = lambda n: lambda x: t_((n, x))

optional = lambda i: dict(i, optional=True)

t_int = t_('int')
t_double = t_('double')
t_text = t_('text')
t_bool = t_('bool')

t_ref = lambda ref: t_(('ref', ref))


t_array = tc_('array')
t_sum = lambda *r: tc_('sum')(r)
t_record = lambda *f: tc_('record')(f)
t_tuple = lambda *f: tc_('tuple')(f)

t_unit = t_tuple()
t_either = lambda a, b: t_sum(('Left', a), ('Right', b))
