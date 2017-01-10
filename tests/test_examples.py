from nstack import build
from helper_defs import *

example = {
 "types": {"Either": t_either(t_int, t_int),
           "Pair": t_tuple(t_int, t_int),
           "Record": t_record(('fst', t_int), ('snd', t_int)),
           "Optional": optional(t_int)},
 "signatures": {"method1": [optional(t_tuple(t_ref('Record'), t_tuple(t_int, t_int, t_int))),
                            t_tuple()]}}


def test_process_schema():
    a, b = build.process_schema(example)
