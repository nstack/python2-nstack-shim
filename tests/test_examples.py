import pytest

from nstack import build
from helper_defs import *

example = {
 "types": {"Either": t_either(t_int, t_int),
           "Pair": t_tuple(t_int, t_int),
           "Record": t_record(('fst', t_int), ('snd', t_int)),
           "Optional": optional(t_int)},
 "signatures": {"method1": [optional(t_tuple(t_ref('Record'), t_tuple(t_int, t_int, t_int))),
                            t_text]}}

def _object_with_method(method, name=None, cls_name=None):
    return type(cls_name or 'Obj', (object, ), {(name or method.__name__): method})()


def test_process_schema():
    a, b = build.process_schema(example)
    x = b(_object_with_method((lambda self, i: repr(i)), name='method1'))
    # slightly brittle, but will do for now...
    assert x.method1(({'fst': 3, 'snd': 4}, (1, 2, 5))) == "(Record(fst='fst', snd='snd'), (1, 2, 5))"
    assert x.method1(None) == "None"

def test_sums():
    a, b = build.process_schema(example)
    x = a['Either'].new((1, 3))
    assert isinstance(x, a['Either'])
    assert isinstance(x, a['Either'].Right)
    assert not isinstance(x, a['Either'].Left)
    assert x.valueWithIndex() == (1, 3)
    assert x.getRight() == 3
    with pytest.raises(TypeError):
        x.getLeft()
    assert x.match(lambda a: False,
                   lambda a: True)
    assert not x.match(lambda a: True,
                       lambda a: False)
    assert x.match(lambda i: i,
                   lambda i: i * 3) == 9
    assert x.value == 3

    assert isinstance(a['Either'].Left(3), a['Either'].Left)
    assert not isinstance(a['Either'].Left(3), a['Either'].Right)

def test_optional():
    a, b = build.process_schema(example)
    assert a['Optional'](None) is None
    assert a['Optional'](3) == 3
    with pytest.raises(ValueError):
        a['Optional']("string")

def test_nested_sum():
    a, b = build.process_schema({'types': {'Foo': t_sum(('A', t_int), ('B', t_bool))},
                                 'signatures': {'method1': [
                                     t_tuple(t_int, t_record(('a', t_bool), ('b', t_ref('Foo')))),
                                     t_tuple(t_ref('Foo'))]}})
    x = b(_object_with_method((lambda self, i: i[1][1]), name='method1'))
    assert x.method1((1, (2, (1, False)))) == (1, False)
    assert x.method1((1, (2, (0, 3)))) == (0, 3)

