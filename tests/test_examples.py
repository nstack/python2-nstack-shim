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
