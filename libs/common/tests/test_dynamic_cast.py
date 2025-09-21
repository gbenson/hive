import pytest

from hive.common import dynamic_cast


class A(object):
    pass


class B(A):
    pass


class C:
    pass


class D(C):
    pass


class E(A):
    pass


class F(object):
    pass


@pytest.mark.parametrize("typ", (A, B, C, D, E, F))
@pytest.mark.parametrize("cls", (A, B, C, D, E, F))
def test_dynamic_cast(typ: type, cls: type) -> None:
    val = cls()
    if isinstance(val, typ):
        assert dynamic_cast(typ, val) is val
    else:
        with pytest.raises(TypeError) as ex:
            _ = dynamic_cast(typ, val)
        assert str(ex.value) == cls.__name__
