from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import json
import pytest
from nstack import build
from helper_defs import *

testdata1 = json.loads("""
{
  "config": {
    "runCmd": "/usr/bin/true",
    "stack": "Python"
  },
  "api": {
    "types": [
      [ [ "nstack/Hello:0.0.1-SNAPSHOT", "MyText" ], { "type": [ "text", null ] } ],
      [ [ "nstack/Hello2:0.0.1-SNAPSHOT", "MyInt" ], { "type": [ "int", null ] } ]
    ],
    "imports": [ [ "One", "nstack/Hello:0.0.1-SNAPSHOT" ] ],
    "signatures": {
      "numChars": [
        { "type": [ "ref", ["nstack/Hello:0.0.1-SNAPSHOT", "MyText"] ] },
        { "type": [ "ref", ["nstack/Hello2:0.0.1-SNAPSHOT", "MyInt"] ] }
      ]
    },
    "unqualified": [
      "nstack/Hello2:0.0.1-SNAPSHOT"
    ]
  }
}""")

testdata2 = {
    "types": [[["nstack/Ex1:0.0.1", "Foo"], t_tuple(t_int, t_int)],
              [["nstack/Ex2:0.0.1", "Foo"], t_tuple(t_ref(["nstack/Ex1:0.0.1", "Foo"]),
                                                    t_ref(["nstack/Ex1:0.0.1", "Foo"]))]],
    "signatures": {"method1": [t_ref(["nstack/Ex1:0.0.1", "Foo"]),
                               t_ref(["nstack/Ex2:0.0.1", "Foo"])]},
    "imports": [["Ex1", "nstack/Ex1:0.0.1"], ["Ex2", "nstack/Ex2:0.0.1"]],
    "unqualified": ["nstack/Ex3:0.0.1"],
}

def test_namespace1():
    a, b, c = build.process_schema(testdata1["api"])
    assert issubclass(c.MyInt, int)
    assert issubclass(c.One.MyText, str)
    with pytest.raises(AttributeError):
        c.MyText
    assert b(type('ex', (object, ), {'numChars': lambda i: len(i)})).numChars("foo") == 3


def test_namespace2():
    a, b, c = build.process_schema(testdata2)
    assert c.Ex1.Foo is not c.Ex2.Foo
    with pytest.raises(AttributeError):
        c.Foo
    assert b(type('ex', (object, ), {'method1': lambda i: (i, i)})).method1((1,2)) == ((1,2), (1,2))
