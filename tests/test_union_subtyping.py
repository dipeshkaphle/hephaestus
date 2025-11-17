import pytest
from src.ir import types as tp
from src.ir import typescript_types as tst

# Helper classes for testing
class SuperType(tp.SimpleClassifier):
    def __init__(self, name="SuperType"):
        super().__init__(name)

class TypeA(tp.SimpleClassifier):
    def __init__(self, name="TypeA"):
        super().__init__(name, supertypes=[SuperType()])

class SubTypeOfA(tp.SimpleClassifier):
    def __init__(self, name="SubTypeOfA"):
        super().__init__(name, supertypes=[TypeA()])

class TypeB(tp.SimpleClassifier):
    def __init__(self, name="TypeB"):
        super().__init__(name, supertypes=[SuperType()])

class UnrelatedType(tp.SimpleClassifier):
    def __init__(self, name="UnrelatedType"):
        super().__init__(name)

def test_subtype_is_subtype_of_union():
    """
    Verifies the fix for two_way_subtyping.
    SubTypeOfA <: TypeA <: (TypeA | TypeB) should be True.
    """
    type_a = TypeA()
    type_b = TypeB()
    sub_type_of_a = SubTypeOfA()
    union_type = tst.UnionType([type_a, type_b])

    assert sub_type_of_a.is_subtype(union_type), \
        "FIX FAILED: Subtype of a union member should be a subtype of the union."

def test_direct_member_is_subtype_of_union():
    """
    Tests if a direct member of a union is a subtype of the union.
    TypeA <: (TypeA | TypeB) should be True.
    """
    type_a = TypeA()
    type_b = TypeB()
    union_type = tst.UnionType([type_a, type_b])

    assert type_a.is_subtype(union_type), \
        "A direct member of a union should be a subtype of the union."

def test_unrelated_type_is_not_subtype_of_union():
    """
    Tests that an unrelated type is not a subtype of a union.
    UnrelatedType <: (TypeA | TypeB) should be False.
    """
    type_a = TypeA()
    type_b = TypeB()
    unrelated_type = UnrelatedType()
    union_type = tst.UnionType([type_a, type_b])

    assert not unrelated_type.is_subtype(union_type), \
        "An unrelated type should not be a subtype of the union."

def test_union_is_subtype_of_common_supertype():
    """
    Tests if a union is a subtype of a common supertype.
    (TypeA | TypeB) <: SuperType should be True, since TypeA <: SuperType and TypeB <: SuperType.
    """
    type_a = TypeA()
    type_b = TypeB()
    super_type = SuperType()
    union_type = tst.UnionType([type_a, type_b])

    assert union_type.is_subtype(super_type), \
        "A union should be a subtype of a type that is a supertype of all its members."

def test_union_is_not_subtype_of_partial_supertype():
    """
    Tests that a union is not a subtype of a type that is only a supertype of some of its members.
    (TypeA | UnrelatedType) <: SuperType should be False, since UnrelatedType is not a subtype of SuperType.
    """
    type_a = TypeA()
    unrelated_type = UnrelatedType()
    super_type = SuperType()
    union_type = tst.UnionType([type_a, unrelated_type])

    assert not union_type.is_subtype(super_type), \
        "A union should not be a subtype of a type unless all its members are subtypes."

def test_union_is_subtype_of_super_union():
    """
    Tests subtyping between two union types.
    (SubTypeOfA | TypeB) <: (TypeA | TypeB) should be True.
    """
    type_a = TypeA()
    type_b = TypeB()
    sub_type_of_a = SubTypeOfA()

    sub_union = tst.UnionType([sub_type_of_a, type_b])
    super_union = tst.UnionType([type_a, type_b])

    assert sub_union.is_subtype(super_union), \
        "A union should be a subtype of another union if all its members are subtypes of the other union."

def test_original_xl8eg_bug_scenario():
    """
    Re-running the original verification test to ensure the fix doesn't break it.
    This test should continue to pass.
    """
    G = tp.TypeParameter("G")
    daffier_type = tst.StringLiteralType("daffier")
    O_bound = tst.UnionType([G, daffier_type])
    O = tp.TypeParameter("O", bound=O_bound)

    object_type = tst.ObjectType()
    target_union = tst.UnionType([object_type, daffier_type])

    is_subtype_result = O.is_subtype(target_union)

    assert not is_subtype_result, \
        "The original bug condition should still evaluate to False."
