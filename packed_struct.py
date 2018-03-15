import re
import struct
from collections import OrderedDict, namedtuple
from warnings import warn

class Field:
    def __init_subclass__(cls, format):
        cls.format = format

    def __init__(self, allowed=None):
        self.allowed = allowed

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance._tuple, self.name)

    def __set__(self, instance, value):
        raise AttributeError

    def __delete__(self, instance):
        raise AttributeError

    def __repr__(self):
        return "{}<'{}'>".format(self.__class__.__qualname__, self.format)


class Struct:
    def __init_subclass__(cls):
        cls._fields = OrderedDict((k, v) for (k, v) in cls.__dict__.items() if isinstance(v, Field))

        cls._Tuple = namedtuple(cls.__name__ + 'Tuple', cls._fields.keys())

    def __init__(self, buff, offset=0):
        self._buffer = buff

        self._size = 0
        self._offset = offset
        t = []
        for _, f in self._fields.items():
            t.append(struct.unpack_from(f.format, buff, offset)[0])
            size = struct.calcsize(f.format)
            offset += size
            self._size += size

        self._tuple = self._Tuple(*t)

        for name, field in self._fields.items():
            if field.allowed is not None:
                if getattr(self, name) not in field.allowed:
                    warn("Field {} has invalid value {}".format(name, getattr(self, name)))
    
    def __repr__(self):
        return re.sub(r'{}\((.*)\)'.format(self._Tuple.__name__),
                      r'{}<\1>'.format(self.__class__.__name__),
                      self._tuple.__str__())

class F:
    class uint16le(Field, format="<H"):
        pass

    class ubyte(Field, format="B"):
        pass

    class bytes(Field, format="{:d}s"):
        def __init__(self, n, allowed=None):
            super().__init__(allowed)

            self.format = self.format.format(n)

    class uint32le(Field, format="<L"):
        pass
