from collections import namedtuple

id_ = lambda i: i
const = lambda i: lambda x: i

class SumBase(object):
    pass

class RecordBase(object):
    pass

class NStackTypeInputMixin(object):
    @classmethod
    def _nstackFromBase(cls, base):
        raise NotImplementedError("_nstackFromBase not implemented")

class NStackTypeOutputMixin(object):
    def _nstackToBase(self):
        raise NotImplementedError("_nstackToBase not implemented")

def createlist(name, preprocfunc=None, optional=False):
    class ListProxy(list):
        def __new__(cls, a=None):
            if a is None and optional:
                return None
            return list.__new__(cls, a)
        def __init__(self, a):
            if preprocfunc:
                a = preprocfunc(a)
            super(ListProxy, self).__init__(a)
    return type(name, (ListProxy, ), {})

def createtuple(name, length, preprocfunc=None, optional=False):
    class TupleProxy(tuple):
        def __new__(cls, a=None):
            if a is None and optional:
                # python's tuple type supports `tuple()`
                # which returns the empty tuple. we lose
                # that semantics because of ambiguity
                # with an optional empty tuple
                return None
            if preprocfunc:
                a = preprocfunc(a)
            r = tuple.__new__(cls, a)
            if len(r) < length:
                raise TypeError("tuple type too small")
            return r
    return type(name, (TupleProxy, ), {})

def createrecord(name, fields, preprocfunc=None, optional=False):
    # fields is a mapping of name to constructor
    nt = namedtuple(name, fields)
    class TupleProxy(nt, RecordBase):
        def __new__(cls, a):
            # intermediate class needed for use of super
            if a is None and optional:
                return None
            if preprocfunc:
                a = preprocfunc(a)
            return super(TupleProxy, cls).__new__(cls, *a)

    return type(name, (TupleProxy, ), {})

def createsum(name, constrs, preprocfuncs=None, optional=False):
    # constrs is a mapping of constr name to constructor
    subclasses = []

    raiseOnTypeError = object()

    class Sum(SumBase, NStackTypeInputMixin, NStackTypeOutputMixin):
        def __init__(self, value):
            raise RuntimeError("Calling constructor of sum type base-class")

        @classmethod
        def new(cls, v):
            if v is None and optional:
                return None
            branch_idx, value = v
            return subclasses[branch_idx](value)

        def match(self, *args):
            return self._church(args)

        @property
        def value(self):
            return self.match(*(id_ for i in subclasses))

        def valueWithIndex(self):
            return self.match(*((lambda i: lambda v: (i, v))(i)
                                for i, j in enumerate(subclasses)))

        @property
        def _branch(self):
            return self.match(*(const(i) for i in range(len(subclasses))))

        def _getAs(self, cls, default=raiseOnTypeError):
            err = raiseTypeError(cls.__name__) if default is raiseOnTypeError else const(default)
            return self.match(*((id_ if cls is j else err) for j in subclasses))

        def _isA(self, cls):
            return self.match(*((lambda v: cls is j) for j in subclasses))

        def __repr__(self):
            return "<{}: {}({})>".format(name, self._constructor_name, self.value)

        @classmethod
        def _nstackFromBase(cls, v):
            return cls.new(v)

        def _nstackToBase(self):
            return self.valueWithIndex()

    def raiseTypeError(name):
        def inner(v):
            raise TypeError("Not a " + name)
        return inner

    def makeconstructor(i):
        def constructor(self, value):
            if preprocfuncs:
                value = preprocfuncs[i](value)
            self._church = lambda args: args[i](value)
        return constructor

    base_ = type(name, (Sum, ), {})

    for i, j in enumerate(constrs):
        branch = type(j, (base_, ), {
            '__init__': makeconstructor(i),
            '_constructor_name': j})
        subclasses.append(branch)
        setattr(base_, j, branch)
        setattr(base_, "get" + j, (lambda branch_:
            lambda self, default=raiseOnTypeError: self._getAs(branch_, default=default))(branch))
        setattr(base_, "is" + j, (lambda branch_: lambda self: self._isA(branch))(branch))
    return base_
