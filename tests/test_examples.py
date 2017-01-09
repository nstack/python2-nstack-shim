import nstack.build

example = {
 "types": {"Either": {"type": ["sum", ["Left", None, "Right", None]]},
 "Pair": {"type": ["tuple", [None, None]]},
 "Record": {"type": ["record", [["fst", {"type": ["ref", "Either"]}],
                                ["snd", {"type": ["ref", "Pair"]}]]]},
 "Optional": {"optional": True}},
 "signatures": {"method1": [{"type": ["tuple", [{"type": ["ref", "Record"]},
                                                {"type": ["tuple", [None, None, None]]}]],
                             "optional": True},
                            {"type": ["tuple", []]}]}}

